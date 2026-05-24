"""Hermes plugin: /tvoice voice preset switching.

User-local Hermes plugin that registers an in-session slash command with
ctx.register_command(). It edits profile-level Hermes config only; it does not
modify Hermes source files under ~/.hermes/hermes-agent/**.
"""
from __future__ import annotations

import contextlib
import functools
import io
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable, Optional, cast

logger = logging.getLogger(__name__)

PRESETS: dict[str, dict[str, str]] = {
    "ua-ostap": {
        "provider": "edge",
        "voice": "uk-UA-OstapNeural",
        "label": "Ukrainian Ostap",
        "lang": "uk",
    },
    "pl-marek": {
        "provider": "edge",
        "voice": "pl-PL-MarekNeural",
        "label": "Polish Marek",
        "lang": "pl",
    },
}

ALIASES = {
    "ua": "ua-ostap",
    "uk": "ua-ostap",
    "ukrainian": "ua-ostap",
    "ostap": "ua-ostap",
    "українська": "ua-ostap",
    "укр": "ua-ostap",
    "pl": "pl-marek",
    "polish": "pl-marek",
    "marek": "pl-marek",
    "польська": "pl-marek",
    "пол": "pl-marek",
}

UK_HINTS = set("іїєґІЇЄҐ")
PL_HINTS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
PL_WORDS = {
    "cześć", "czesc", "jest", "się", "sie", "nie", "tak", "proszę", "prosze",
    "dziękuję", "dziekuje", "mówi", "mowimy", "mówimy", "polsku", "polski", "polska",
}
UK_WORDS = {
    "привіт", "дякую", "українською", "українська", "україна", "говоримо",
    "будь", "ласка", "так", "ні", "що", "це", "цей", "можна", "буде",
}

_RUNTIME_FOOTER_SEP = " · "
_PERCENT_RE = re.compile(r"^(?:100|\d{1,2})%$")
_TELEGRAM_CONVERTIBLE_AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".aac"}
_EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"  # symbols and pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport/map
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u27BF"          # misc symbols + dingbats (✅, ❤️, etc.)
    "\U0001F3FB-\U0001F3FF"  # skin tones
    "\uFE0E\uFE0F\u200D\u20E3"  # variation selectors, ZWJ, keycap
    "]+"
)
_ASCII_EMOTICON_RE = re.compile(
    r"(?<!\w)(?:[:;=8xX][-o*']?[)\](\[dDpP/:}{@|\\]|"
    r"[)\](\[dDpP/:}{@|\\][-o*']?[:;=8xX])(?!\w)"
)
# Keep this policy in sync with the Hermes skill `telegram-voice`, pitfall
# "Footer or emoji read aloud by TTS". The plugin implements deterministic
# runtime sanitization; the skill documents the workflow for future maintainers.


def _looks_like_runtime_footer(line: str) -> bool:
    """Return True for Hermes runtime footer lines such as `gpt · 17% · ~/cwd`."""
    stripped = (line or "").strip()
    if not stripped or "\n" in stripped or _RUNTIME_FOOTER_SEP not in stripped:
        return False
    if len(stripped) > 180:
        return False

    parts = [part.strip() for part in stripped.split(_RUNTIME_FOOTER_SEP) if part.strip()]
    if len(parts) < 2:
        return False

    has_context_percent = any(_PERCENT_RE.fullmatch(part) for part in parts)
    has_cwd = any(
        part == "~"
        or part.startswith(("~/", "/"))
        or part in {".", ".."}
        for part in parts
    )
    # The default footer has model + context% + cwd. Custom footers may omit
    # one field, but requiring either the context percentage or a path keeps
    # ordinary `foo · bar` prose intact.
    return has_context_percent or has_cwd


def _strip_footer_for_tts(text: str) -> str:
    """Remove Hermes runtime footer from text before it is fed to TTS.

    Gateway text still keeps the footer when enabled; this only prevents voice
    replies from reading "gpt dot seventeen percent dot cwd" aloud.
    """
    if not text or _RUNTIME_FOOTER_SEP not in text:
        return text

    lines = text.rstrip().splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and _looks_like_runtime_footer(lines[-1]):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines).rstrip()
    return text


def _strip_emoji_for_tts(text: str) -> str:
    """Remove emoji/smileys that TTS providers tend to spell out aloud."""
    if not text:
        return text
    cleaned = _EMOJI_RE.sub(" ", text)
    cleaned = _ASCII_EMOTICON_RE.sub(" ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _sanitize_text_for_tts(text: str) -> str:
    """Prepare visible reply text for speech without mutating the chat text.

    Telegram still receives the normal text reply/caption. This sanitizer is
    only used for the speech synthesis path, where runtime footers and emoji
    are noise ("gpt dot 17 percent dot cwd", "smiling face", etc.).
    """
    if not text:
        return text
    # Strip emoji first because users/skins may put an icon at the start of the
    # runtime footer line. Then remove the now-plain footer from the end.
    cleaned = _strip_emoji_for_tts(text)
    cleaned = _strip_footer_for_tts(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _convert_audio_to_telegram_voice(audio_path: str) -> str:
    """Convert an audio file to Telegram-native OGG/Opus if possible.

    Returns the converted `.ogg` path on success. On failure, returns the
    original path so Telegram can still fall back to sendAudio/document.
    """
    path = Path(audio_path).expanduser()
    ext = path.suffix.lower()
    if ext in {".ogg", ".opus"}:
        return str(path)
    if ext not in _TELEGRAM_CONVERTIBLE_AUDIO_EXTS:
        return str(path)
    if not path.exists() or not path.is_file():
        return str(path)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        logger.warning("telegram-tvoice: ffmpeg missing; cannot convert %s to OGG/Opus", path)
        return str(path)

    out_path = path.with_name(f"{path.stem}.telegram-voice-{uuid.uuid4().hex[:8]}.ogg")
    cmd = [
        ffmpeg,
        "-i", str(path),
        "-acodec", "libopus",
        "-ac", "1",
        "-b:a", "64k",
        "-vbr", "off",
        str(out_path),
        "-y",
        "-loglevel", "error",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
    except Exception as exc:
        logger.warning("telegram-tvoice: OGG/Opus conversion failed for %s: %s", path, exc)
        return str(path)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore")[:300]
        logger.warning("telegram-tvoice: ffmpeg conversion failed for %s: %s", path, stderr)
        with contextlib.suppress(OSError):
            out_path.unlink()
        return str(path)
    if not out_path.exists() or out_path.stat().st_size <= 0:
        logger.warning("telegram-tvoice: ffmpeg produced empty OGG for %s", path)
        with contextlib.suppress(OSError):
            out_path.unlink()
        return str(path)
    return str(out_path)


def _install_tts_text_filter() -> None:
    """Patch Hermes' TTS entrypoints so voice replies skip footer/emoji.

    Gateway auto-TTS calls BasePlatformAdapter.prepare_tts_text() before it
    calls tools.tts_tool.text_to_speech_tool(). Direct/manual TTS tool calls can
    bypass that gateway method. Patch both plugin-locally so the rule is stable
    without editing live Hermes source.
    """
    try:
        from tools import tts_tool  # type: ignore[import-not-found]
    except Exception as exc:
        logger.debug("telegram-tvoice: could not import tools.tts_tool: %s", exc)
        tts_tool = None

    if tts_tool is not None and not getattr(tts_tool, "_telegram_tvoice_text_filter_installed", False):
        original_strip = cast(Optional[Callable[[str], str]], getattr(tts_tool, "_strip_markdown_for_tts", None))
        if callable(original_strip):
            @functools.wraps(original_strip)
            def _filtered_strip_markdown_for_tts(text: str) -> str:
                return original_strip(_sanitize_text_for_tts(text))

            setattr(_filtered_strip_markdown_for_tts, "_telegram_tvoice_original", original_strip)
            tts_tool._strip_markdown_for_tts = _filtered_strip_markdown_for_tts

        original_tts = cast(Optional[Callable[..., Any]], getattr(tts_tool, "text_to_speech_tool", None))
        if callable(original_tts):
            @functools.wraps(original_tts)
            def _filtered_text_to_speech_tool(
                text: str,
                output_path: str | None = None,
                *args,
                **kwargs,
            ) -> str:
                return original_tts(_sanitize_text_for_tts(text), output_path, *args, **kwargs)

            setattr(_filtered_text_to_speech_tool, "_telegram_tvoice_original", original_tts)
            tts_tool.text_to_speech_tool = _filtered_text_to_speech_tool

        tts_tool._telegram_tvoice_text_filter_installed = True

    try:
        from gateway.platforms.base import BasePlatformAdapter  # type: ignore[import-not-found]
    except Exception as exc:
        logger.debug("telegram-tvoice: could not import BasePlatformAdapter: %s", exc)
        return

    if getattr(BasePlatformAdapter, "_telegram_tvoice_prepare_tts_filter_installed", False):
        return
    original_prepare = cast(Optional[Callable[..., str]], getattr(BasePlatformAdapter, "prepare_tts_text", None))
    if not callable(original_prepare):
        return

    @functools.wraps(original_prepare)
    def _filtered_prepare_tts_text(self, text: str) -> str:
        prepared = original_prepare(self, _sanitize_text_for_tts(text))
        return _sanitize_text_for_tts(prepared)

    setattr(_filtered_prepare_tts_text, "_telegram_tvoice_original", original_prepare)
    BasePlatformAdapter.prepare_tts_text = _filtered_prepare_tts_text
    BasePlatformAdapter._telegram_tvoice_prepare_tts_filter_installed = True


def _install_tts_footer_filter() -> None:
    """Backward-compatible alias for older plugin tests/imports."""
    _install_tts_text_filter()


def _install_telegram_voice_delivery_patch() -> None:
    """Patch TelegramAdapter.send_voice to upload OGG/Opus voice bubbles.

    Hermes core already *tries* to make Telegram TTS OGG, but when a caller hands
    the Telegram adapter an MP3 directly, the adapter routes it through
    sendAudio. This plugin-level shim converts that MP3/M4A/WAV/FLAC one last
    time right before Telegram upload, without touching live Hermes source.
    """
    try:
        from gateway.platforms.telegram import TelegramAdapter  # type: ignore[import-not-found]
    except Exception as exc:
        logger.debug("telegram-tvoice: could not import TelegramAdapter: %s", exc)
        return

    if getattr(TelegramAdapter, "_telegram_tvoice_ogg_patch_installed", False):
        return

    original = TelegramAdapter.send_voice

    @functools.wraps(original)
    async def _send_voice_ogg_first(
        self,
        chat_id: str,
        audio_path: str,
        caption: str | None = None,
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ):
        converted_path: str | None = None
        original_path = str(audio_path)
        send_path = original_path
        converted = _convert_audio_to_telegram_voice(original_path)
        if converted != original_path and Path(converted).exists():
            converted_path = converted
            send_path = converted

        try:
            return await original(
                self,
                chat_id,
                send_path,
                caption=caption,
                reply_to=reply_to,
                metadata=metadata,
                **kwargs,
            )
        finally:
            if converted_path:
                with contextlib.suppress(OSError):
                    os.unlink(converted_path)

    TelegramAdapter.send_voice = _send_voice_ogg_first
    TelegramAdapter._telegram_tvoice_ogg_patch_installed = True


def _usage() -> str:
    return (
        "TVoice commands:\n"
        "  /tvoice status\n"
        "  /tvoice ua-ostap\n"
        "  /tvoice pl-marek\n"
        "  /tvoice auto <text>\n"
        "  /tvoice preset <alias>\n\n"
        "Aliases: ua, uk, ostap, pl, marek. This is profile-level voice switching; "
        "the next TTS generation should use the selected voice."
    )


def _split_args(raw_args: str) -> list[str]:
    raw = (raw_args or "").strip()
    if not raw:
        return ["status"]
    try:
        parts = shlex.split(raw)
    except ValueError:
        parts = raw.split()
    if not parts:
        return ["status"]
    if parts[0].lower() == "preset" and len(parts) > 1:
        parts = parts[1:]
    return parts


def _set_config_value(key: str, value: str) -> None:
    """Set a Hermes config value while swallowing CLI-style stdout."""
    from hermes_cli.config import set_config_value

    with contextlib.redirect_stdout(io.StringIO()):
        set_config_value(key, value)


def _ensure_preset_config() -> None:
    for name, data in PRESETS.items():
        _set_config_value(f"tts.voice_presets.{name}.provider", data["provider"])
        _set_config_value(f"tts.voice_presets.{name}.voice", data["voice"])
        _set_config_value(f"tts.voice_presets.{name}.label", data["label"])
    _set_config_value("tts.auto_voice_by_language", "true")
    _set_config_value("tts.language_voice_map.uk", "ua-ostap")
    _set_config_value("tts.language_voice_map.pl", "pl-marek")


def _apply_preset(raw_name: str) -> str:
    name = ALIASES.get(raw_name.lower().strip(), raw_name.lower().strip())
    if name not in PRESETS:
        known = ", ".join(sorted(PRESETS))
        return f"❌ Unknown preset '{raw_name}'. Known: {known}"

    data = PRESETS[name]
    _set_config_value("tts.provider", data["provider"])
    _set_config_value("tts.edge.voice", data["voice"])
    _set_config_value("tts.default_voice_preset", name)
    _ensure_preset_config()
    return (
        f"✅ active Edge TTS preset -> {name} ({data['voice']})\n"
        "Next TTS reply should use the selected voice."
    )


def _detect_language(text: str) -> str | None:
    lower = text.lower()
    uk_score = sum(2 for ch in text if ch in UK_HINTS)
    pl_score = sum(2 for ch in text if ch in PL_HINTS)
    for word in UK_WORDS:
        if word in lower:
            uk_score += 3
    for word in PL_WORDS:
        if word in lower:
            pl_score += 3
    cyrillic_count = sum(1 for ch in text if "а" <= ch.lower() <= "я" or ch in "іїєґІЇЄҐ")
    latin_count = sum(1 for ch in text if "a" <= ch.lower() <= "z" or ch in PL_HINTS)
    if cyrillic_count >= 8 and pl_score < 4:
        uk_score += 2
    if pl_score >= uk_score + 2 and pl_score >= 3:
        return "pl"
    if uk_score >= pl_score + 2 and uk_score >= 3:
        return "uk"
    if cyrillic_count >= 12 and cyrillic_count > latin_count:
        return "uk"
    return None


def _auto(text: str) -> str:
    lang = _detect_language(text)
    if lang == "pl":
        return _apply_preset("pl-marek")
    if lang == "uk":
        return _apply_preset("ua-ostap")
    return "⚠️ No confident language match; current preset unchanged."


def _status() -> str:
    from hermes_cli.config import get_config_path, get_env_value, load_config

    cfg = load_config() or {}
    tts = cfg.get("tts") or {}
    stt = cfg.get("stt") or {}
    edge = tts.get("edge") or {}
    groq = stt.get("groq") or {}
    lang_map = tts.get("language_voice_map") or {}

    ffmpeg = "missing"
    try:
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "missing"
    except Exception:
        pass

    return "\n".join([
        "TVoice status:",
        f"- Config: {get_config_path()}",
        f"- TTS provider: {tts.get('provider', 'unknown')}",
        f"- Active voice: {edge.get('voice', 'unknown')}",
        f"- Default preset: {tts.get('default_voice_preset', 'unknown')}",
        f"- Auto language map: uk={lang_map.get('uk', 'n/a')}, pl={lang_map.get('pl', 'n/a')}",
        f"- STT provider: {stt.get('provider', 'unknown')}",
        f"- Groq model: {groq.get('model', 'unknown')}",
        f"- Groq key: {'present' if get_env_value('GROQ_API_KEY') else 'missing'}",
        f"- ffmpeg: {ffmpeg}",
    ])


def handle_tvoice(raw_args: str) -> str:
    parts = _split_args(raw_args)
    cmd = parts[0].lower()
    if cmd in {"help", "-h", "--help"}:
        return _usage()
    if cmd in {"status", "presets", "list"}:
        return _status()
    if cmd == "auto":
        text = " ".join(parts[1:]).strip()
        if not text:
            return "❌ /tvoice auto needs text. Example: /tvoice auto Cześć, mówimy po polsku"
        return _auto(text)
    return _apply_preset(cmd)


def _promote_tvoice_in_telegram_menu() -> None:
    """Keep /tvoice visible in Telegram's capped BotCommand menu.

    Hermes currently builds the Telegram menu from core commands first, then
    caps the BotCommand payload at 30 entries. Plugin commands are still
    dispatchable when typed manually, but can be trimmed from the visible menu.
    Mutating the in-memory priority tuple here is a plugin-only workaround that
    avoids editing live Hermes source under ~/.hermes/hermes-agent/**.
    """
    try:
        from importlib import import_module

        commands = import_module("hermes_cli.commands")
        raw_priority = getattr(commands, "_TELEGRAM_MENU_PRIORITY", ()) or ()
        current: list[str] = [str(name) for name in raw_priority if str(name) != "tvoice"]
        for anchor in ("status", "commands", "help"):
            if anchor in current:
                current.insert(current.index(anchor) + 1, "tvoice")
                break
        else:
            current.insert(0, "tvoice")
        setattr(commands, "_TELEGRAM_MENU_PRIORITY", tuple(current))
    except Exception:
        # Menu promotion is best-effort; the command itself remains registered.
        pass


def register(ctx):
    _install_tts_text_filter()
    _install_telegram_voice_delivery_patch()
    _promote_tvoice_in_telegram_menu()
    ctx.register_command(
        "tvoice",
        handle_tvoice,
        "Switch Telegram/CLI Edge TTS voice preset: status, ua-ostap, pl-marek, auto <text>",
        args_hint="status|ua-ostap|pl-marek|auto <text>",
    )
