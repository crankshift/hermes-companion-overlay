# telegram-tvoice troubleshooting

## `/tvoice` is not recognized

- Enable the plugin: `hermes plugins enable telegram-tvoice`
- Restart the CLI session or gateway after enabling
- Verify `$HERMES_HOME/plugins/telegram-tvoice/plugin.yaml` and `__init__.py` exist
- If using a symlinked plugin root, check `realpath "$HERMES_HOME/plugins/telegram-tvoice"`
- If the Telegram command menu does not show `/tvoice`, type it manually; Telegram menus are capped and gateway restart may be needed for the promoted menu order

## Groq key is missing

Groq is only needed for STT from Telegram voice notes. Edge TTS and `/tvoice` voice switching work without it.

```bash
hermes config set GROQ_API_KEY '<your-groq-api-key>'
hermes gateway restart
```

Then check `/tvoice status`.

## Telegram sends an audio attachment instead of a round voice bubble

Telegram native voice bubbles require OGG/Opus. The plugin converts MP3/M4A/WAV/FLAC just before `TelegramAdapter.send_voice` when `ffmpeg` is available.

Check:

```bash
ffmpeg -version
```

The plugin uses this conversion shape:

```bash
ffmpeg -nostdin -y -loglevel error -i input.mp3 -acodec libopus -ac 1 -b:a 64k -vbr off output.ogg
```

If conversion fails or `ffmpeg` is missing, the plugin returns the original audio path so Hermes can still send an attachment.

## Voice changed in config but Telegram still uses the old voice

`/tvoice` writes profile-level config. A long-running gateway may keep stale config in memory.

```bash
hermes gateway restart
```

If you are in the CLI, exit and relaunch Hermes.

## Footer, emoji, or smileys are spoken aloud

The plugin patches both gateway auto-TTS preparation and direct TTS tool entrypoints. Restart after updating the plugin, then verify the current runtime has loaded it with `/tvoice status`.

If the text reply still shows the footer or emoji, that is expected; the sanitizer is only for the speech synthesis path.
