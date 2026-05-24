"""Runtime Edge TTS voice catalog for telegram-tvoice."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
import inspect
import threading
from typing import Any


@dataclass(frozen=True)
class Voice:
    short_name: str
    locale: str
    gender: str
    friendly_name: str
    personalities: tuple[str, ...] = ()


@dataclass(frozen=True)
class VoiceCatalog:
    voices: tuple[Voice, ...]
    source: str
    error: str | None = None


FALLBACK_VOICES: tuple[Voice, ...] = (
    Voice(
        short_name="uk-UA-OstapNeural",
        locale="uk-UA",
        gender="Male",
        friendly_name="Microsoft Ostap Online (Natural) - Ukrainian (Ukraine)",
        personalities=("Warm",),
    ),
    Voice(
        short_name="uk-UA-PolinaNeural",
        locale="uk-UA",
        gender="Female",
        friendly_name="Microsoft Polina Online (Natural) - Ukrainian (Ukraine)",
        personalities=("Friendly",),
    ),
    Voice(
        short_name="pl-PL-MarekNeural",
        locale="pl-PL",
        gender="Male",
        friendly_name="Microsoft Marek Online (Natural) - Polish (Poland)",
        personalities=("Clear",),
    ),
    Voice(
        short_name="pl-PL-ZofiaNeural",
        locale="pl-PL",
        gender="Female",
        friendly_name="Microsoft Zofia Online (Natural) - Polish (Poland)",
        personalities=("Friendly",),
    ),
    Voice(
        short_name="en-US-AndrewNeural",
        locale="en-US",
        gender="Male",
        friendly_name="Microsoft Andrew Online (Natural) - English (United States)",
        personalities=("Warm",),
    ),
    Voice(
        short_name="en-US-AvaNeural",
        locale="en-US",
        gender="Female",
        friendly_name="Microsoft Ava Online (Natural) - English (United States)",
        personalities=("Expressive",),
    ),
)

_VOICE_CACHE: VoiceCatalog | None = None


def _run_awaitable(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result: dict[str, Any] = {}

    def run_in_thread() -> None:
        try:
            result["value"] = asyncio.run(awaitable)
        except BaseException as exc:  # pragma: no cover - defensive bridge
            result["error"] = exc

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _fetch_edge_voices() -> Any:
    import edge_tts

    raw = edge_tts.list_voices()
    if inspect.isawaitable(raw):
        raw = _run_awaitable(raw)
    return raw


def _coerce_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value if item)
    return (str(value),)


def _voice_personalities(raw: dict[str, Any]) -> tuple[str, ...]:
    voice_tag = raw.get("VoiceTag") or raw.get("voice_tag") or {}
    if not isinstance(voice_tag, dict):
        return ()
    personalities = voice_tag.get("VoicePersonalities") or voice_tag.get("voice_personalities")
    return _coerce_strings(personalities)


def normalize_voice(raw: Any) -> Voice | None:
    if isinstance(raw, Voice):
        return raw
    if not isinstance(raw, dict):
        return None

    short_name = str(raw.get("ShortName") or raw.get("short_name") or "").strip()
    if not short_name:
        return None

    locale = str(raw.get("Locale") or raw.get("locale") or "").strip()
    gender = str(raw.get("Gender") or raw.get("gender") or "").strip()
    friendly_name = str(
        raw.get("FriendlyName")
        or raw.get("friendly_name")
        or raw.get("Name")
        or raw.get("name")
        or short_name
    ).strip()
    return Voice(
        short_name=short_name,
        locale=locale,
        gender=gender,
        friendly_name=friendly_name,
        personalities=_voice_personalities(raw),
    )


def _normalize_voices(raw_voices: Any) -> tuple[Voice, ...]:
    voices: list[Voice] = []
    for raw_voice in raw_voices or []:
        voice = normalize_voice(raw_voice)
        if voice is not None:
            voices.append(voice)
    return tuple(sorted(voices, key=lambda voice: voice.short_name.lower()))


def get_voice_catalog(refresh: bool = False) -> VoiceCatalog:
    global _VOICE_CACHE
    if _VOICE_CACHE is not None and not refresh:
        return _VOICE_CACHE

    try:
        voices = _normalize_voices(_fetch_edge_voices())
        if voices:
            _VOICE_CACHE = VoiceCatalog(voices=voices, source="runtime")
            return _VOICE_CACHE
        error = "edge_tts.list_voices returned no voices"
    except Exception as exc:  # pragma: no cover - exact edge_tts failures vary
        error = str(exc) or exc.__class__.__name__

    _VOICE_CACHE = VoiceCatalog(voices=FALLBACK_VOICES, source="fallback", error=error)
    return _VOICE_CACHE


def refresh_voice_catalog() -> VoiceCatalog:
    return get_voice_catalog(refresh=True)


def _voice_search_text(voice: Voice) -> str:
    return " ".join(
        [
            voice.short_name,
            voice.locale,
            voice.gender,
            voice.friendly_name,
            " ".join(voice.personalities),
        ]
    ).lower()


def _locale_segments(voice: Voice) -> tuple[str, ...]:
    return tuple(segment for segment in voice.locale.lower().replace("_", "-").split("-") if segment)


def _matches_voice_term(voice: Voice, term: str) -> bool:
    if term in {"male", "female"}:
        return voice.gender.lower() == term
    if len(term) == 2 and term.isalpha():
        return term in _locale_segments(voice)
    if "-" in term and voice.locale.lower().replace("_", "-") == term:
        return True
    return term in _voice_search_text(voice)


def search_voices(voices: Iterable[Voice], query: str | Iterable[str]) -> list[Voice]:
    if isinstance(query, str):
        terms = [term.lower() for term in query.split() if term.strip()]
    else:
        terms = [str(term).lower() for term in query if str(term).strip()]
    if not terms:
        return list(voices)
    return [voice for voice in voices if all(_matches_voice_term(voice, term) for term in terms)]


def find_voice(voices: Iterable[Voice], short_name: str) -> Voice | None:
    needle = short_name.strip().lower()
    for voice in voices:
        if voice.short_name.lower() == needle:
            return voice
    return None
