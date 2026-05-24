"""Hermes plugin: /tvoice Edge TTS voice switching.

User-local Hermes plugin that registers an in-session slash command with
ctx.register_command(). It edits profile-level Hermes config only; it does not
modify Hermes source files under ~/.hermes/hermes-agent/**.
"""
from __future__ import annotations

from .audio import _convert_audio_to_telegram_voice
from .commands import (
    _auto,
    _detect_language,
    _split_args,
    _status,
    _usage,
    handle_tvoice,
)
from .patches import (
    TVOICE_MENU_DESCRIPTION,
    _install_telegram_voice_delivery_patch,
    _install_tts_footer_filter,
    _install_tts_text_filter,
    _promote_tvoice_in_telegram_menu,
)
from .sanitizer import (
    _looks_like_runtime_footer,
    _sanitize_text_for_tts,
    _strip_emoji_for_tts,
    _strip_footer_for_tts,
)

__all__ = [
    "_auto",
    "_convert_audio_to_telegram_voice",
    "_detect_language",
    "_install_telegram_voice_delivery_patch",
    "_install_tts_footer_filter",
    "_install_tts_text_filter",
    "_looks_like_runtime_footer",
    "_promote_tvoice_in_telegram_menu",
    "_sanitize_text_for_tts",
    "_split_args",
    "_status",
    "_strip_emoji_for_tts",
    "_strip_footer_for_tts",
    "_usage",
    "handle_tvoice",
    "register",
]


def register(ctx) -> None:
    _install_tts_text_filter()
    _install_telegram_voice_delivery_patch()
    _promote_tvoice_in_telegram_menu()
    ctx.register_command(
        "tvoice",
        handle_tvoice,
        TVOICE_MENU_DESCRIPTION,
        args_hint="status|list [country-code|query]|set <voice-id>|refresh|auto <text>",
    )
