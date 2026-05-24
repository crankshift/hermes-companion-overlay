# telegram-tvoice plugin — fresh install runbook

This is the portable install note for the `telegram-tvoice` Hermes user plugin.

Goal: install a user-local Hermes plugin that adds `/tvoice` for switching Edge TTS voices between Ukrainian Ostap and Polish Marek, with optional Groq Whisper STT for Telegram voice messages.

Current plugin behavior:

- `/tvoice` switches profile-level Edge TTS presets.
- Telegram voice replies are forced through an OGG/Opus conversion shim before upload when Hermes hands Telegram an MP3/M4A/WAV/FLAC path.
- Hermes runtime footer lines such as `gpt-5.5 · 17% · ~/workspace` and emoji/smileys are stripped from TTS input so the text reply/caption can keep them while the spoken voice does not read them aloud.
- The sanitizer is installed at both gateway auto-TTS (`BasePlatformAdapter.prepare_tts_text`) and direct TTS-tool entrypoints; patching only `tools.tts_tool._strip_markdown_for_tts` is not enough for Telegram voice replies.
- Keep the implementation in sync with the Hermes skill `telegram-voice` (pitfall: "Footer or emoji read aloud by TTS"). The plugin implements the runtime rule; the skill is a human/agent runbook, not code that executes during audio delivery.

Important boundaries:

- Do not edit live Hermes source under `~/.hermes/hermes-agent/**` or another active install source tree unless explicitly requested.
- Do not create `~/.hermes/scripts` helper folders for this flow.
- Install the plugin under Hermes' user plugin root (`~/.hermes/plugins/telegram-tvoice`) unless the current machine has a discovered repo/symlink convention.
- If a repo-backed plugin root is used, document it with placeholders such as `<plugin-repo>`; do not hardcode usernames, machine names, or private repo names in this common runbook.
- Secrets go to `~/.hermes/.env` via Hermes config/env commands, not into this plugin directory.

## 1. Prerequisites

Install/configure Hermes first:

```bash
hermes setup
hermes doctor
```

For Telegram voice bubbles and audio conversion, install `ffmpeg` with libopus support:

```bash
# Debian/Ubuntu/Termux-proot style
sudo apt update
sudo apt install -y ffmpeg

# Verify
ffmpeg -version
```

For Groq STT you need a Groq API key:

```bash
hermes config set GROQ_API_KEY '<your-groq-api-key>'
```

Edge TTS needs no API key.

## 2. Put the plugin in Hermes' user plugin root

Hermes discovers user plugins under `~/.hermes/plugins/`. The portable direct-install layout is:

```text
~/.hermes/plugins/telegram-tvoice/
├── plugin.yaml
├── __init__.py
├── INSTALL.md
└── tests/
```

If you are migrating from another machine, copy the folder:

```bash
mkdir -p ~/.hermes/plugins
cp -a /path/to/telegram-tvoice ~/.hermes/plugins/telegram-tvoice
```

Do not copy `__pycache__/`; it is generated junk.

### Optional repo-backed layout

If the current machine keeps plugins in a dotfiles repo or shared project repo, use a variable or placeholder instead of a hardcoded private path:

```bash
PLUGIN_REPO=/path/to/your/hermes-plugins
mkdir -p "$PLUGIN_REPO"
cp -a /path/to/telegram-tvoice "$PLUGIN_REPO/telegram-tvoice"

# Optional: expose the whole repo as Hermes' user plugin root.
# Only do this after moving/merging any existing ~/.hermes/plugins contents.
ln -s "$PLUGIN_REPO" ~/.hermes/plugins
```

If `~/.hermes/plugins` already exists as a real directory, migrate it safely instead of nuking it blindly:

```bash
PLUGIN_REPO=/path/to/your/hermes-plugins
mkdir -p "$PLUGIN_REPO"

# Move any existing plugins into the chosen repo first.
# If there are no existing plugins, this command may print an error; that is okay.
mv ~/.hermes/plugins/* "$PLUGIN_REPO"/ 2>/dev/null || true

# Replace the now-empty runtime plugin directory with a symlink.
rmdir ~/.hermes/plugins
ln -s "$PLUGIN_REPO" ~/.hermes/plugins
```

Expected checks:

```bash
realpath ~/.hermes/plugins
realpath ~/.hermes/plugins/telegram-tvoice
python -m py_compile ~/.hermes/plugins/telegram-tvoice/__init__.py
```

## 3. Enable the plugin

```bash
hermes plugins enable telegram-tvoice
```

Expected config fragment in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - telegram-tvoice
  disabled: []
```

Restart the CLI session or gateway after enabling:

```bash
# CLI: exit and launch hermes again
hermes

# Gateway/service:
hermes gateway restart
# or from Telegram/admin chat:
/restart
```

## 4. Configure STT: Telegram voice note -> text

Use Groq Whisper:

```bash
hermes config set stt.enabled true
hermes config set stt.provider groq
hermes config set stt.groq.model whisper-large-v3-turbo
hermes config set GROQ_API_KEY '<your-groq-api-key>'
```

Expected config:

```yaml
stt:
  enabled: true
  provider: groq
  groq:
    model: whisper-large-v3-turbo
```

## 5. Configure TTS: text -> Edge voice

Base Edge TTS config:

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice uk-UA-OstapNeural
hermes config set tts.edge.speed 1.0
hermes config set voice.auto_tts false
```

Preset config used by `/tvoice`:

```bash
hermes config set tts.default_voice_preset ua-ostap
hermes config set tts.voice_presets.ua-ostap.provider edge
hermes config set tts.voice_presets.ua-ostap.voice uk-UA-OstapNeural
hermes config set tts.voice_presets.ua-ostap.label 'Ukrainian Ostap'
hermes config set tts.voice_presets.pl-marek.provider edge
hermes config set tts.voice_presets.pl-marek.voice pl-PL-MarekNeural
hermes config set tts.voice_presets.pl-marek.label 'Polish Marek'
hermes config set tts.auto_voice_by_language true
hermes config set tts.language_voice_map.uk ua-ostap
hermes config set tts.language_voice_map.pl pl-marek
```

Expected config:

```yaml
tts:
  provider: edge
  edge:
    voice: uk-UA-OstapNeural
    speed: 1.0
  default_voice_preset: ua-ostap
  voice_presets:
    ua-ostap:
      provider: edge
      voice: uk-UA-OstapNeural
      label: Ukrainian Ostap
    pl-marek:
      provider: edge
      voice: pl-PL-MarekNeural
      label: Polish Marek
  auto_voice_by_language: true
  language_voice_map:
    uk: ua-ostap
    pl: pl-marek

voice:
  auto_tts: false
```

`voice.auto_tts: false` is intentional: use `/voice tts` per chat when you want spoken replies, rather than forcing every chat into audio.

## 6. Telegram gateway basics

Telegram itself must already be configured in Hermes gateway setup:

```bash
hermes gateway setup
hermes gateway status
```

Typical secret is the Telegram bot token in `~/.hermes/.env`; do not commit it to a plugin repo.

If using the gateway service:

```bash
hermes gateway restart
```

Then in the target Telegram chat:

```text
/voice tts
/tvoice status
/tvoice ua-ostap
/tvoice pl-marek
/tvoice auto Cześć, mówimy po polsku
/tvoice auto Привіт, говоримо українською
```

## 7. Skills to add for future agents

The plugin works without skills. Skills are for agents so they remember the correct workflow.

Recommended skills on a new machine:

- `hermes-agent` — usually bundled with Hermes; load before Hermes config/plugin work.
- `telegram-voice` — portable Telegram voice workflow skill; install/copy it if missing.

Check:

```bash
hermes skills list
```

If `telegram-voice` is missing, copy/install the skill into the Hermes skills tree, for example:

```bash
mkdir -p ~/.hermes/skills/common
cp -a /path/to/common/telegram-voice ~/.hermes/skills/common/telegram-voice
```

Do not put plugin helper code into skills. Skills are docs/procedures; plugin code lives in the plugin directory.

## 8. Verification

Plugin discovery smoke test:

```bash
python - <<'PY'
from hermes_cli.plugins import get_plugin_manager, get_plugin_commands, get_plugin_command_handler, resolve_plugin_command_result
pm = get_plugin_manager()
pm.discover_and_load(force=True)
print('registered=', 'tvoice' in get_plugin_commands())
handler = get_plugin_command_handler('tvoice')
print('handler=', bool(handler))
if handler:
    print(resolve_plugin_command_result(handler('status')))
PY
```

Expected:

```text
registered= True
handler= True
TVoice status:
- TTS provider: edge
- Active voice: uk-UA-OstapNeural
- Default preset: ua-ostap
- STT provider: groq
- Groq model: whisper-large-v3-turbo
- Groq key: present
- ffmpeg: /usr/bin/ffmpeg
```

Command tests:

```bash
# In CLI/gateway session:
/tvoice status
/tvoice pl-marek
/tvoice ua-ostap
/tvoice auto Cześć, mówimy po polsku
/tvoice auto Привіт, говоримо українською
```

Config check after switching:

```bash
hermes config
```

Python/unit smoke test from the plugin directory:

```bash
python -m unittest discover -s ~/.hermes/plugins/telegram-tvoice/tests -v
```

## 9. Troubleshooting

### `/tvoice` is not recognized

- Run `hermes plugins enable telegram-tvoice`.
- Restart Hermes CLI or gateway.
- Verify `~/.hermes/plugins/telegram-tvoice/plugin.yaml` and `__init__.py` exist.
- If using a symlinked plugin root, run `realpath ~/.hermes/plugins` and verify it resolves to the intended repo.

### Groq key missing

Run:

```bash
hermes config set GROQ_API_KEY '<your-groq-api-key>'
/restart
```

### Voice changed in config but Telegram still uses old voice

The plugin changes profile-level config. Restart gateway once if the running gateway has cached config:

```bash
hermes gateway restart
```

True per-chat/no-restart voice state requires Hermes core support via gateway session context; this plugin is intentionally source-free and profile-level.

### Telegram sends audio attachment instead of round voice bubble

Telegram native voice bubbles need Opus in `.ogg`/`.opus`. Verify ffmpeg exists:

```bash
ffmpeg -version
```

Known-good conversion shape:

```bash
ffmpeg -i input.mp3 -acodec libopus -ac 1 -b:a 64k -vbr off output.ogg -y
```

If Hermes core does not convert Edge MP3 output to OGG/Opus for Telegram, that needs core adapter/TTS work, not a plugin config fix.

## 10. Update workflow

Canonical edit path is the plugin directory discovered on the current machine:

```bash
realpath ~/.hermes/plugins/telegram-tvoice
```

If the machine uses a repo-backed plugin root, edit the repo target shown by `realpath` rather than creating a second copy.

After code changes:

```bash
python -m py_compile ~/.hermes/plugins/telegram-tvoice/__init__.py
python -m unittest discover -s ~/.hermes/plugins/telegram-tvoice/tests -v
hermes gateway restart
# or restart CLI session
```

Do not edit generated `__pycache__` files, do not commit secrets, and do not resurrect `~/.hermes/scripts` for this plugin. GPIO-кишка закрита.
