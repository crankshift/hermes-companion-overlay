"""TTS text cleanup helpers for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

import re

_RUNTIME_FOOTER_SEP = " · "
_PERCENT_RE = re.compile(r"^(?:100|\d{1,2})%$")
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
    "\u2600-\u27BF"          # misc symbols + dingbats
    "\U0001F3FB-\U0001F3FF"  # skin tones
    "\uFE0E\uFE0F\u200D\u20E3"  # variation selectors, ZWJ, keycap
    "]+"
)
_ASCII_EMOTICON_RE = re.compile(
    r"(?<!\w)(?:[:;=8xX][-o*']?[)\](\[dDpP/:}{@|\\]|"
    r"[)\](\[dDpP/:}{@|\\][-o*']?[:;=8xX])(?!\w)"
)


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
    return has_context_percent or has_cwd


def _strip_footer_for_tts(text: str) -> str:
    """Remove a Hermes runtime footer from text before it is fed to TTS."""
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
    """Prepare visible reply text for speech without mutating the chat text."""
    if not text:
        return text
    # Strip emoji first because users/skins may put an icon at the start of the
    # runtime footer line. Then remove the now-plain footer from the end.
    cleaned = _strip_emoji_for_tts(text)
    cleaned = _strip_footer_for_tts(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
