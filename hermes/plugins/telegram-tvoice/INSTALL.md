# telegram-tvoice install runbook

`telegram-tvoice` is a user-local Hermes plugin that adds `/tvoice` for switching Telegram/CLI Edge TTS between Ukrainian Ostap and Polish Marek. It also strips Hermes runtime footers and emoji from spoken TTS, and tries to convert Telegram TTS audio to OGG/Opus voice bubbles before upload.

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

TTS preset switching:

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice uk-UA-OstapNeural
hermes config set tts.default_voice_preset ua-ostap
hermes config set voice.auto_tts false
```

Optional Telegram voice-note STT with Groq:

```bash
hermes config set stt.enabled true
hermes config set stt.provider groq
hermes config set stt.groq.model whisper-large-v3-turbo
hermes config set GROQ_API_KEY '<your-groq-api-key>'
```

`/tvoice ua-ostap`, `/tvoice pl-marek`, and `/tvoice auto <text>` will write the full preset map when used.

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

Then try:

```text
/tvoice status
/tvoice list
/tvoice ua-ostap
/tvoice pl-marek
/tvoice auto Cześć, mówimy po polsku
/tvoice auto Привіт, говоримо українською
```

See `TROUBLESHOOTING.md` for runtime failure modes and `DEVELOPMENT.md` for source maintenance notes.
