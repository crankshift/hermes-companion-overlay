# telegram-tvoice development

This plugin stays source-only in this repository. Do not edit live `$HERMES_HOME` files, secrets, sessions, logs, caches, or generated state while developing it here.

## Module Map

- `__init__.py`: thin Hermes registration shim and compatibility re-exports
- `constants.py`: language hints
- `sanitizer.py`: footer, emoji, and smiley cleanup for TTS input
- `audio.py`: Telegram OGG/Opus conversion helper
- `commands.py`: `/tvoice` parsing, status, auto language detection, config writes
- `voice_catalog.py`: dynamic Edge TTS voice discovery, normalization, cache, and fallback catalog
- `patches.py`: Hermes TTS, Telegram delivery, and Telegram menu monkey-patch installers
- `tests/`: package-loader based unit tests for the multi-file plugin layout

## Source And Runtime Boundary

- Keep source edits under `hermes/plugins/telegram-tvoice/`
- Do not write secrets, API keys, logs, local databases, or generated profile state here
- Do not validate by mutating live `$HERMES_HOME`; use mocked config modules in tests
- Runtime install steps belong in `INSTALL.md`; failure modes belong in `TROUBLESHOOTING.md`

## Test Commands

Run from the repository root:

```bash
python3 -m py_compile hermes/plugins/telegram-tvoice/*.py
python3 -m unittest discover -s hermes/plugins/telegram-tvoice/tests -v
```

The real ffmpeg conversion test may skip when `ffmpeg` or `ffprobe` are unavailable. The command-shape test still verifies the plugin builds the intended ffmpeg invocation.

## Implementation Notes

- Use package-relative imports between plugin modules
- Keep `register(ctx)` small: install patches, promote the menu, register `/tvoice`
- Patch installers must be idempotent because plugin registration can be repeated in tests or a reloaded runtime
- `_install_telegram_voice_delivery_patch()` must return cleanly when `TelegramAdapter.send_voice` is missing or not callable
- Audio conversion must keep ffmpeg options before the output path and include `-nostdin`
- `/tvoice list [country-code|query]` searches the Edge TTS voice catalog; a two-letter country/region query such as `ua` shows all matching locale-region voices without the default 20-item cap
- `/tvoice set <edge-voice-id>` should only write `tts.provider` and `tts.edge.voice`
- Shortcut aliases such as `ua-ostap`, `pl-marek`, `ua`, and `pl` are intentionally not supported as set commands or presets

Do not commit `__pycache__/`, test artifacts, secrets, or runtime-generated files.
