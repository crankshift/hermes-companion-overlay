"""Slash-command handling for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

import contextlib
import io
import shlex
import shutil

from .constants import ALIASES, PL_HINTS, PL_WORDS, PRESETS, UK_HINTS, UK_WORDS


def _aliases_for_preset(name: str) -> list[str]:
    return sorted(alias for alias, preset in ALIASES.items() if preset == name)


def _format_preset_list() -> str:
    lines = ["Available TVoice presets:"]
    for name in sorted(PRESETS):
        data = PRESETS[name]
        aliases = ", ".join(_aliases_for_preset(name))
        alias_text = f" aliases: {aliases}" if aliases else ""
        lines.append(f"- {name}: {data['label']} ({data['provider']} / {data['voice']});{alias_text}")
    return "\n".join(lines)


def _usage() -> str:
    return (
        "TVoice commands:\n"
        "  /tvoice status\n"
        "  /tvoice list\n"
        "  /tvoice presets\n"
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
        return f"Unknown preset '{raw_name}'. Known: {known}"

    data = PRESETS[name]
    _set_config_value("tts.provider", data["provider"])
    _set_config_value("tts.edge.voice", data["voice"])
    _set_config_value("tts.default_voice_preset", name)
    _ensure_preset_config()
    return (
        f"active Edge TTS preset -> {name} ({data['voice']})\n"
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
    return "No confident language match; current preset unchanged."


def _status() -> str:
    from hermes_cli.config import get_config_path, get_env_value, load_config

    cfg = load_config() or {}
    tts = cfg.get("tts") or {}
    stt = cfg.get("stt") or {}
    edge = tts.get("edge") or {}
    groq = stt.get("groq") or {}
    lang_map = tts.get("language_voice_map") or {}
    ffmpeg = shutil.which("ffmpeg") or "missing"

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
    if cmd == "status":
        return _status()
    if cmd in {"presets", "list"}:
        return _format_preset_list()
    if cmd == "auto":
        text = " ".join(parts[1:]).strip()
        if not text:
            return "/tvoice auto needs text. Example: /tvoice auto Cześć, mówimy po polsku"
        return _auto(text)
    return _apply_preset(cmd)
