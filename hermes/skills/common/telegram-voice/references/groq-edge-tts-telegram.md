# Groq + Edge TTS Telegram Voice Notes

Session-derived notes from planning a Hermes Telegram voice improvement.

## Goal pattern

- Inbound Telegram voice notes should transcribe through **Groq Whisper**.
- Outbound spoken replies should use **Edge TTS**.
- Default personal/profile voice can be Ukrainian Ostap: `uk-UA-OstapNeural`.
- Runtime switching should allow alternatives such as Polish Marek: `pl-PL-MarekNeural`.
- Switching should not require a gateway restart.
- Telegram voice replies should be native voice bubbles, meaning Opus audio in `.ogg` / `.opus`.

## Source facts observed

Hermes already has these relevant pieces:

- `tools/transcription_tools.py`
  - Supports `provider: groq`.
  - Uses `GROQ_API_KEY`.
  - Default Groq model is `whisper-large-v3-turbo`.
  - Explicit provider selection should be authoritative; do not silently cross-fallback to another cloud provider when the explicit provider is missing credentials.

- `tools/tts_tool.py`
  - Default provider is Edge TTS.
  - Reads `tts:` config.
  - Detects Telegram through session platform context.
  - Converts Edge MP3 to OGG Opus for Telegram voice compatibility when ffmpeg is available.

- `gateway/platforms/telegram.py`
  - `.ogg` / `.opus` files are sent with Telegram `send_voice`.
  - `.mp3` / `.m4a` files are sent with `send_audio`.

- `gateway/run.py`
  - Has `/voice` command state with per-chat modes: `off`, `voice_only`, `all`.
  - Persists voice mode in `gateway_voice_mode.json`.

- `gateway/session_context.py`
  - Uses `ContextVar`s to avoid process-global session state bleed.
  - This is the right pattern for per-chat/per-turn TTS overrides.

## Suggested config

```yaml
stt:
  enabled: true
  provider: groq
  groq:
    model: whisper-large-v3-turbo

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
```

## Runtime command sketch

Preferred core-command UX when editing Hermes core in a safe checkout:

```text
/voice tts
/voice preset
/voice presets
/voice preset ua-ostap
/voice preset pl-marek
/voice preset reset
/voice status
```

No-core-edit plugin fallback:

```text
/voicepreset ua-ostap
/voicepreset pl-marek
/voicepreset status
```

Hermes general plugins can register slash commands with `ctx.register_command(name, handler, description)`. These commands work in CLI and gateway contexts and are surfaced in help/autocomplete/Telegram bot menus. Built-in command names win conflicts, so a plugin should not try to replace `/voice`; use a separate command name. Plugin handlers are enough for profile/global config toggles or helper-script calls, but not proven sufficient for clean per-chat/per-topic TTS context injection without core support.

## Implementation hotspots

Likely code files:

- `tools/transcription_tools.py` — only if `stt.groq.model` lookup needs improvement.
- `tools/tts_tool.py` — voice preset resolution and session override merge.
- `gateway/run.py` — `/voice preset` command handling and per-chat state.
- `gateway/session_context.py` — context vars for runtime TTS provider/preset/voice overrides.
- `hermes_cli/config.py` — default config/comments for Groq and voice presets.
- `hermes_cli/commands.py` — help/subcommand registry updates.
- `gateway/platforms/telegram.py` — only if Telegram send behavior/menu needs updates.

Likely test files:

- `tests/tools/test_transcription_tools.py`
- `tests/tools/test_tts_tool.py`
- `tests/gateway/test_voice_command.py`
- `tests/gateway/test_session_context_tts_overrides.py`
- Telegram platform delivery tests under `tests/gateway/` or `tests/gateway/platforms/`

## Test targets

- Explicit `provider: groq` selects Groq and respects `stt.groq.model`.
- Missing `GROQ_API_KEY` fails clearly and does not fall back to OpenAI/local.
- Edge TTS uses runtime voice override when session context supplies one.
- Telegram platform context triggers OGG/Opus output/conversion.
- `.ogg` / `.opus` delivery goes through Telegram `send_voice`.
- `/voice preset <alias>` updates in-memory and persisted state without gateway restart.
- Parallel chats/topics cannot bleed voice overrides into each other.

## Audio conversion command

```bash
ffmpeg -i input.mp3 -acodec libopus -ac 1 -b:a 64k -vbr off output.ogg -y
```

If ffmpeg/libopus is absent, capture the fix as an install/setup step; do not encode a durable claim that Telegram voice or Edge TTS is broken.

## Important ambiguity

The phrase “groqk” is probably a typo for **Groq**, not xAI **Grok**. Confirm if it affects implementation, because Groq and Grok use different credentials/providers.
