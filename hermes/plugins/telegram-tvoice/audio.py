"""Audio conversion helpers for Telegram voice-note delivery."""
from __future__ import annotations

import contextlib
import logging
import shutil
import subprocess
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_TELEGRAM_CONVERTIBLE_AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".aac"}


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
        "-nostdin",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-acodec",
        "libopus",
        "-ac",
        "1",
        "-b:a",
        "64k",
        "-vbr",
        "off",
        str(out_path),
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
