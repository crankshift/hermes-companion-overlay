# telegram-tvoice install runbook

`telegram-tvoice` is a user-local Hermes plugin that adds `/tvoice` for switching Telegram/CLI Edge TTS voices by real Edge voice ID. It also strips Hermes runtime footers and emoji from spoken TTS, and tries to convert Telegram TTS audio to OGG/Opus voice bubbles before upload.

This repository is source-only. Runtime activation happens by copying or linking this plugin folder into `$HERMES_HOME/plugins/telegram-tvoice`; do not symlink the whole repository over `$HERMES_HOME`.

## Prerequisites

- Hermes is installed and working: `hermes doctor`
- `ffmpeg` with libopus is installed if you want Telegram round voice bubbles
- A Groq API key is available only if you want Telegram voice-note STT
- Edge TTS needs no API key

## Install The Plugin

From this repository root:

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins"
cp -a hermes/plugins/telegram-tvoice "$HERMES_HOME/plugins/telegram-tvoice"
```

For a repo-backed install, use a symlink to this plugin folder instead:

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins"
ln -s "$PWD/hermes/plugins/telegram-tvoice" "$HERMES_HOME/plugins/telegram-tvoice"
```

If `$HERMES_HOME/plugins/telegram-tvoice` already exists, inspect it first and replace it deliberately.

## Enable

```bash
hermes plugins enable telegram-tvoice
```

Expected runtime config shape:

```yaml
plugins:
  enabled:
    - telegram-tvoice
```

## Minimal Config

TTS voice switching:

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice uk-UA-OstapNeural
hermes config set voice.auto_tts false
```

Optional Telegram voice-note STT with Groq:

```bash
hermes config set stt.enabled true
hermes config set stt.provider groq
hermes config set stt.groq.model whisper-large-v3-turbo
hermes config set GROQ_API_KEY '<your-groq-api-key>'
```

`/tvoice list [country-code|query]` searches the runtime Edge TTS catalog, `/tvoice list ua` shows all voices with region `UA`, `/tvoice set <voice-id>` selects a real Edge voice ID such as `uk-UA-OstapNeural` or `en-US-AndrewNeural`, and `/tvoice refresh` refetches the in-memory catalog. The plugin falls back to a small bundled catalog when `edge_tts` voice discovery is unavailable.

## Source-Only Verification

These checks run against this repository and do not mutate live `$HERMES_HOME`:

```bash
python3 -m py_compile hermes/plugins/telegram-tvoice/*.py
python3 -m unittest discover -s hermes/plugins/telegram-tvoice/tests -v
```

## Restart And Smoke Test

Restart Hermes after enabling or updating the plugin:

```bash
hermes gateway restart
```

Or exit and relaunch the CLI session.

If Telegram still shows an old `/tvoice` description after a gateway restart, check `TROUBLESHOOTING.md` for stale chat-scoped BotCommand overrides. A specific DM chat scope can override the updated default or `all_private_chats` menu until `deleteMyCommands` is run for that chat.

Then try:

```text
/tvoice status
/tvoice list
/tvoice list en male
/tvoice set en-US-AndrewNeural
/tvoice set uk-UA-OstapNeural
/tvoice refresh
/tvoice auto Cześć, mówimy po polsku
/tvoice auto Привіт, говоримо українською
/tvoice auto Hello, this is English
```

See `TROUBLESHOOTING.md` for runtime failure modes and `DEVELOPMENT.md` for source maintenance notes.
