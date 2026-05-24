"""Runtime patch installers for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

import contextlib
import functools
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional, cast

from .audio import _convert_audio_to_telegram_voice
from .sanitizer import _sanitize_text_for_tts

logger = logging.getLogger(__name__)

TVOICE_MENU_DESCRIPTION = "Switch Edge TTS voice: status, list [query], set <voice-id>, refresh"


def _install_tts_text_filter() -> None:
    """Patch Hermes' TTS entrypoints so voice replies skip footer/emoji."""
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
                *args: Any,
                **kwargs: Any,
            ) -> Any:
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
    def _filtered_prepare_tts_text(self: Any, text: str) -> str:
        prepared = original_prepare(self, _sanitize_text_for_tts(text))
        return _sanitize_text_for_tts(prepared)

    setattr(_filtered_prepare_tts_text, "_telegram_tvoice_original", original_prepare)
    BasePlatformAdapter.prepare_tts_text = _filtered_prepare_tts_text
    BasePlatformAdapter._telegram_tvoice_prepare_tts_filter_installed = True


def _install_tts_footer_filter() -> None:
    """Backward-compatible alias for older plugin tests/imports."""
    _install_tts_text_filter()


def _install_telegram_voice_delivery_patch() -> None:
    """Patch TelegramAdapter.send_voice to upload OGG/Opus voice bubbles."""
    try:
        from gateway.platforms.telegram import TelegramAdapter  # type: ignore[import-not-found]
    except Exception as exc:
        logger.debug("telegram-tvoice: could not import TelegramAdapter: %s", exc)
        return

    if getattr(TelegramAdapter, "_telegram_tvoice_ogg_patch_installed", False):
        return

    original = getattr(TelegramAdapter, "send_voice", None)
    if not callable(original):
        logger.debug("telegram-tvoice: TelegramAdapter.send_voice is missing or not callable")
        return

    @functools.wraps(original)
    async def _send_voice_ogg_first(
        self: Any,
        chat_id: str,
        audio_path: str,
        caption: str | None = None,
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
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


def _menu_command_name(command: Any) -> str | None:
    if isinstance(command, dict):
        name = command.get("command") or command.get("name")
        return str(name) if name else None
    if isinstance(command, (tuple, list)) and command:
        return str(command[0])
    name = getattr(command, "command", None) or getattr(command, "name", None)
    return str(name) if name else None


def _tvoice_menu_entry(sample: Any = None) -> Any:
    if isinstance(sample, dict):
        entry = dict(sample)
        if "command" in entry or "name" not in entry:
            entry["command"] = "tvoice"
            entry.pop("name", None)
        else:
            entry["name"] = "tvoice"
        entry["description"] = TVOICE_MENU_DESCRIPTION
        return entry
    if isinstance(sample, tuple):
        if hasattr(sample, "_fields"):
            try:
                return sample.__class__("tvoice", TVOICE_MENU_DESCRIPTION)
            except Exception:
                pass
        return ("tvoice", TVOICE_MENU_DESCRIPTION, *sample[2:])
    if isinstance(sample, list):
        return ["tvoice", TVOICE_MENU_DESCRIPTION, *sample[2:]]
    if sample is not None:
        try:
            return sample.__class__(command="tvoice", description=TVOICE_MENU_DESCRIPTION)
        except Exception:
            try:
                return sample.__class__("tvoice", TVOICE_MENU_DESCRIPTION)
            except Exception:
                pass
    return ("tvoice", TVOICE_MENU_DESCRIPTION)


def _telegram_menu_limit(args: tuple[Any, ...], kwargs: dict[str, Any]) -> int | None:
    raw_limit = kwargs.get("max_commands")
    if raw_limit is None and args:
        raw_limit = args[0]
    if raw_limit is None:
        raw_limit = 30
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return None
    return limit if limit > 0 else None


def _install_tvoice_telegram_menu_wrapper(commands: Any) -> None:
    original = getattr(commands, "telegram_menu_commands", None)
    if not callable(original) or getattr(original, "_telegram_tvoice_menu_patch_installed", False):
        return

    @functools.wraps(original)
    def _telegram_menu_commands_with_tvoice(*args: Any, **kwargs: Any) -> Any:
        raw_result = original(*args, **kwargs)
        commands_list = list(raw_result or [])
        sample = commands_list[0] if commands_list else None
        tvoice_entry = _tvoice_menu_entry(sample)
        limit = _telegram_menu_limit(args, kwargs)

        updated: list[Any] = []
        found_tvoice = False
        for command in commands_list:
            if _menu_command_name(command) == "tvoice":
                updated.append(_tvoice_menu_entry(command))
                found_tvoice = True
            else:
                updated.append(command)

        if not found_tvoice:
            if limit is not None and len(updated) >= limit:
                updated = updated[: max(limit - 1, 0)]
            updated.append(tvoice_entry)

        if limit is not None:
            updated = updated[:limit]
        if isinstance(raw_result, tuple):
            return tuple(updated)
        return updated

    setattr(_telegram_menu_commands_with_tvoice, "_telegram_tvoice_menu_patch_installed", True)
    setattr(_telegram_menu_commands_with_tvoice, "_telegram_tvoice_original", original)
    setattr(commands, "telegram_menu_commands", _telegram_menu_commands_with_tvoice)


def _promote_tvoice_in_telegram_menu() -> None:
    """Keep /tvoice visible in Telegram's capped BotCommand menu."""
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
        _install_tvoice_telegram_menu_wrapper(commands)
    except Exception:
        # Menu promotion is best-effort; the command itself remains registered.
        pass
