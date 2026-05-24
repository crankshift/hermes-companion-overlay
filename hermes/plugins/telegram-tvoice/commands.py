"""Slash-command handling for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

import contextlib
import io
import re
import shlex
import shutil

from .constants import EN_WORDS, PL_HINTS, PL_WORDS, UK_HINTS, UK_WORDS
from .voice_catalog import find_voice, get_voice_catalog, refresh_voice_catalog, search_voices


VOICE_LIST_LIMIT = 20
DEFAULT_EN_MALE_VOICE = "en-US-AndrewNeural"
DEFAULT_PL_MALE_VOICE = "pl-PL-MarekNeural"
DEFAULT_UK_MALE_VOICE = "uk-UA-OstapNeural"


def _usage() -> str:
    return (
        "TVoice commands:\n"
        "  /tvoice status\n"
        "  /tvoice list [query]\n"
        "  /tvoice set <edge-voice-id>\n"
        "  /tvoice refresh\n"
        "  /tvoice auto <text>\n\n"
        "Use /tvoice list [query] to find a voice ID, then /tvoice set <edge-voice-id>. "
        "This is profile-level voice switching; the next TTS generation should use the selected voice."
    )


def _format_voice(voice) -> str:
    personality_text = f"; {', '.join(voice.personalities)}" if voice.personalities else ""
    return (
        f"- {voice.short_name}: {voice.friendly_name} "
        f"({voice.locale}, {voice.gender}{personality_text})"
    )


def _format_voice_catalog(query_parts: list[str] | None = None) -> str:
    query = " ".join(query_parts or []).strip()
    catalog = get_voice_catalog()
    matches = search_voices(catalog.voices, query)
    source_text = "runtime catalog" if catalog.source == "runtime" else "fallback catalog"
    heading = "Available Edge TTS voices:"
    if query:
        heading = f"Edge TTS voices matching '{query}':"
    lines = [f"{heading} ({source_text})"]
    if catalog.error:
        lines.append(f"- Catalog note: using fallback after fetch failure: {catalog.error}")
    if not matches:
        lines.append("No matching voices. Try a locale, gender, name, or voice ID.")
        return "\n".join(lines)
    for voice in matches[:VOICE_LIST_LIMIT]:
        lines.append(_format_voice(voice))
    if len(matches) > VOICE_LIST_LIMIT:
        lines.append(
            f"Showing first {VOICE_LIST_LIMIT} of {len(matches)} voices; narrow your query "
            "with locale, gender, name, or ID."
        )
    return "\n".join(lines)


def _format_refresh_result() -> str:
    catalog = refresh_voice_catalog()
    source_text = "runtime catalog" if catalog.source == "runtime" else "fallback catalog"
    lines = [f"Edge TTS voice catalog refreshed: {len(catalog.voices)} voices from {source_text}."]
    if catalog.error:
        lines.append(f"Fetch failed; using fallback: {catalog.error}")
    return "\n".join(lines)


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
    return parts


def _set_config_value(key: str, value: str) -> None:
    """Set a Hermes config value while swallowing CLI-style stdout."""
    from hermes_cli.config import set_config_value

    with contextlib.redirect_stdout(io.StringIO()):
        set_config_value(key, value)


def _known_voice_examples() -> str:
    catalog = get_voice_catalog()
    examples = ", ".join(voice.short_name for voice in catalog.voices[:8])
    if len(catalog.voices) > 8:
        examples = f"{examples}, ..."
    return examples


def _apply_edge_voice(raw_voice_id: str) -> str:
    raw_voice_id = raw_voice_id.strip()
    if not raw_voice_id:
        return "/tvoice set needs an Edge voice ID. Example: /tvoice set en-US-AndrewNeural"

    catalog = get_voice_catalog()
    voice = find_voice(catalog.voices, raw_voice_id)
    if voice is None:
        return (
            f"Unknown Edge voice '{raw_voice_id}'. Known examples: {_known_voice_examples()}\n"
            "Use /tvoice list <query> to search by locale, gender, name, or ID."
        )

    _set_config_value("tts.provider", "edge")
    _set_config_value("tts.edge.voice", voice.short_name)
    return (
        f"active Edge TTS voice -> {voice.short_name}\n"
        "Next TTS reply should use the selected voice."
    )


def _detect_language(text: str) -> str | None:
    lower = text.lower()
    uk_score = sum(2 for ch in text if ch in UK_HINTS)
    pl_score = sum(2 for ch in text if ch in PL_HINTS)
    words = set(re.findall(r"[a-z']+", lower))
    en_score = sum(2 for word in EN_WORDS if word in words)
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
    if en_score >= 4 and latin_count >= 8 and cyrillic_count == 0 and pl_score < 3:
        return "en"
    return None


def _select_default_catalog_voice(locale_prefix: str, gender: str, preferred_voice: str):
    catalog = get_voice_catalog()
    preferred = find_voice(catalog.voices, preferred_voice)
    if preferred is not None:
        return preferred
    matches = search_voices(catalog.voices, [locale_prefix, gender])
    return matches[0] if matches else None


def _auto(text: str) -> str:
    lang = _detect_language(text)
    if lang == "pl":
        voice = _select_default_catalog_voice("pl", "male", DEFAULT_PL_MALE_VOICE)
        if voice is None:
            return "Polish detected, but no Polish male Edge voice is available in the catalog."
        return _apply_edge_voice(voice.short_name)
    if lang == "uk":
        voice = _select_default_catalog_voice("uk", "male", DEFAULT_UK_MALE_VOICE)
        if voice is None:
            return "Ukrainian detected, but no Ukrainian male Edge voice is available in the catalog."
        return _apply_edge_voice(voice.short_name)
    if lang == "en":
        voice = _select_default_catalog_voice("en", "male", DEFAULT_EN_MALE_VOICE)
        if voice is None:
            return "English detected, but no English male Edge voice is available in the catalog."
        return _apply_edge_voice(voice.short_name)
    return "No confident language match; current voice unchanged."


def _status() -> str:
    from hermes_cli.config import get_config_path, get_env_value, load_config

    cfg = load_config() or {}
    tts = cfg.get("tts") or {}
    stt = cfg.get("stt") or {}
    edge = tts.get("edge") or {}
    groq = stt.get("groq") or {}
    ffmpeg = shutil.which("ffmpeg") or "missing"

    return "\n".join([
        "TVoice status:",
        f"- Config: {get_config_path()}",
        f"- TTS provider: {tts.get('provider', 'unknown')}",
        f"- Active voice: {edge.get('voice', 'unknown')}",
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
    if cmd == "list":
        return _format_voice_catalog(parts[1:])
    if cmd == "refresh":
        return _format_refresh_result()
    if cmd == "set":
        voice_id = " ".join(parts[1:]).strip()
        return _apply_edge_voice(voice_id)
    if cmd == "auto":
        text = " ".join(parts[1:]).strip()
        if not text:
            return "/tvoice auto needs text. Example: /tvoice auto Cześć, mówimy po polsku"
        return _auto(text)
    return f"Unknown TVoice command '{parts[0]}'.\n{_usage()}"
