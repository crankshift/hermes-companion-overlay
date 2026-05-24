---
name: telegram-voice
description: "Use when configuring, planning, implementing, or troubleshooting Hermes Agent Telegram voice workflows: voice-message STT, spoken replies/TTS, Groq/Groq Whisper transcription, Edge TTS voices, runtime voice switching, Telegram Opus/OGG voice bubbles, or ffmpeg audio conversion. Load this even if the user only mentions Telegram voice, voice notes, Ostap/Marek, Groq transcription, or mp3 to ogg."
version: 1.0.0
author: Hermes Agent community
license: MIT
metadata:
  hermes:
    tags: [telegram, voice, stt, tts, groq, edge-tts, ffmpeg, hermes-agent]
    related_skills: [hermes-agent]
---

# Telegram Voice Workflows

## Overview

Use this skill for Hermes Telegram voice setup and development work. Telegram voice has two separate paths that often get mixed together:

1. **Inbound voice → text (STT):** Telegram sends voice notes as OGG/Opus. Hermes caches the audio and transcribes it with the configured STT provider.
2. **Outbound text → voice (TTS):** Hermes generates audio from the assistant reply and delivers it back to Telegram. Native Telegram voice bubbles require Opus audio in an `.ogg` / `.opus` container.

Keep those paths mentally separate. Bugs usually come from fixing the wrong half of the pipe, like a drunk GPIO goblin soldering the microphone to the speaker.

## When to Use

Use this skill when the user asks for any of these:

- Configure Telegram voice messages in Hermes Agent.
- Make voice transcription use Groq / Whisper.
- Make replies use Edge TTS.
- Set or switch Edge voices such as `uk-UA-OstapNeural` or `pl-PL-MarekNeural`.
- Make Telegram voice replies appear as round native voice bubbles instead of audio attachments.
- Convert MP3/WAV to Telegram-compatible OGG/Opus.
- Plan or implement live TTS voice switching without gateway restart.
- Add a user-local plugin slash command such as `/tvoice` when core edits are forbidden.
- Add a Telegram voice runbook or user-local skill.

Do **not** use this skill for generic audio editing unrelated to Hermes/Telegram, Spotify/music tasks, or Discord voice-channel-only work unless Telegram delivery is also involved.

## Safety and Scope Rules

- Do not edit the live Hermes install under `~/.hermes/hermes-agent/**` unless the user explicitly asks for live-install surgery. Prefer a source checkout/worktree outside `~/.hermes`.
- Secrets belong in `.env` or `hermes config set`, never in docs, commits, plans, or skills.
- For implementation/testing, isolate state with a temporary `HERMES_HOME` so tests do not touch the user’s real gateway sessions, config, `.env`, or skills.
- Config changes usually need a gateway restart. Runtime voice switching should be implemented as gateway state/session context, not as “edit config and hope cache reloads”.

## Baseline Configuration

For a Groq STT + Edge TTS Telegram setup, the intended user config shape is:

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

voice:
  auto_tts: false
```

Credential:

```bash
hermes config set GROQ_API_KEY <groq-key>
```

Use `voice.auto_tts: false` unless the user wants every chat to get spoken replies by default. Per-chat `/voice tts` is safer.

## Telegram Audio Format Rule

Telegram native voice bubbles require Opus audio in `.ogg` or `.opus`. Edge TTS normally emits MP3, so Hermes should convert the generated file before delivery.

Known-good conversion pattern:

```bash
ffmpeg -i input.mp3 -acodec libopus -ac 1 -b:a 64k -vbr off output.ogg -y
```

Delivery expectations:

- `.ogg` / `.opus` → Telegram adapter should call `send_voice`.
- `.mp3` / `.m4a` → Telegram adapter may call `send_audio` and show an audio attachment, not a native voice bubble.
- If ffmpeg is missing, explain that Telegram voice bubbles need ffmpeg/libopus conversion; do not claim Telegram or Edge TTS is broken.

## Path A+B: No-source personal setup

When the user asks for the safe A+B path, do **not** edit Hermes source. Apply profile-level config and install/use a helper script instead.

Recommended config keys:

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
```

Installed plugin command pattern:

```bash
tvoice status
tvoice list uk male
tvoice set uk-UA-OstapNeural
tvoice list pl male
tvoice set pl-PL-MarekNeural
tvoice auto "Привіт, говоримо українською"
```

Prefer plugin-only for Telegram voice switching: use a profile/user plugin under `~/.hermes/plugins/telegram-tvoice/` or another discovered Hermes plugin root, and do **not** create or leave `~/.hermes/scripts/` helper folders/symlinks for this flow unless the user explicitly asks for a shell helper. Do **not** move personal helpers into hypothetical live-source paths like `~/.hermes/hermes-agent/tools/_user/` or `~/.hermes/hermes-agent/tools/_custom/`; those are not the safe extension surface. If a temporary helper was replaced by a plugin, remove the helper folder and any `~/.local/bin/` aliases that point to it.

Important caveat: this plugin changes profile-level `tts.edge.voice`; it is safe and source-free, but it is not true per-chat runtime state. If the running gateway does not reload TTS config per call, tell the user to `/restart` once. True no-restart per-chat switching still requires Hermes core support via gateway state + `gateway.session_context`.

## Runtime Voice Switching Pattern

For true no-restart per-chat switching, do **not** rely on editing `config.yaml` mid-gateway. Use gateway-owned runtime state and per-turn session context when implementing Hermes core support.

Recommended core command surface:

```text
/voice tts
/voice voices
/voice set <edge-voice-id>
/voice reset
/voice status
```

If core edits are not allowed, use a user-local plugin command instead. Portable plugin layout uses Hermes' user plugin root by default. If the user keeps plugins in a repo, discover that repo and refer to it with a placeholder such as `<plugin-repo>`:

```text
~/.hermes/plugins/telegram-tvoice/
├── plugin.yaml
├── __init__.py
└── INSTALL.md

# Optional repo-backed layout:
<plugin-repo>/telegram-tvoice/
~/.hermes/plugins -> <plugin-repo>
```

Preferred slash command:

```text
/tvoice status
/tvoice list [query]
/tvoice set <edge-voice-id>
/tvoice refresh
/tvoice auto <text>
```

Enable with:

```bash
hermes plugins enable telegram-tvoice
```

Hermes plugins can register slash commands with `ctx.register_command(name, handler, description)` and those commands are exposed in CLI/gateway help, autocomplete, and Telegram bot menus after the plugin is enabled and the session/gateway restarts. Do **not** try to replace the built-in `/voice` command from a plugin: built-in command names win on conflict. A plugin command can safely update profile/global TTS config or call a helper, but true per-chat/per-topic voice overrides may still require core support via gateway state/session context.

Telegram menu caveat: command registration and visible Telegram BotCommand menus are not the same thing. Hermes may cap the visible Telegram menu (observed: 30 commands), so a plugin command can be enabled and manually dispatchable but still absent from Telegram's `/` menu. For `telegram-tvoice`, first verify `get_plugin_commands()` and `telegram_menu_commands(max_commands=30)` before blaming BotFather or plugin loading. If the user wants a plugin-only fix, promote `/tvoice` into Hermes' in-memory Telegram menu priority during plugin `register(ctx)` and then restart the gateway later to publish a new `set_my_commands` payload.

TTS sanitizer caveat: getting Telegram delivery into a real OGG/Opus voice bubble does not guarantee the spoken content is clean. If runtime footers or emoji are read aloud, cover the gateway auto-TTS path (`BasePlatformAdapter.prepare_tts_text`) and direct TTS tool path (`tools.tts_tool.text_to_speech_tool`) in the plugin.

Recommended voice config:

```yaml
tts:
  provider: edge
  edge:
    voice: uk-UA-OstapNeural
```

Implementation guidance:

1. Persist per-chat or per-topic voice preference in gateway-owned state, analogous to existing per-chat voice mode state.
2. Pass the active voice override into the agent/tool turn via `gateway.session_context` `ContextVar`s, not process-global `os.environ`.
3. In the TTS tool, resolve effective provider/voice in this order:
   - session/runtime override
   - configured provider voice, e.g. `tts.edge.voice`
   - built-in fallback
4. Keep state scoped by platform + chat, and consider thread/topic IDs when Telegram topics need independent voices.
5. The switch affects the next TTS generation; it cannot change audio already generated for an in-progress turn.

## Planning Checklist

When writing an implementation plan for Telegram voice improvements, include:

- Goal split into inbound STT and outbound TTS.
- Exact config shape and required env vars.
- Explicit “do not edit `~/.hermes/hermes-agent/**`” boundary if working on Hermes itself.
- Files likely to change: `tools/transcription_tools.py`, `tools/tts_tool.py`, `gateway/run.py`, `gateway/session_context.py`, `hermes_cli/config.py`, `hermes_cli/commands.py`, docs, and tests.
- Tests for explicit STT provider selection and no cross-provider fallback.
- Tests for Telegram Edge TTS generating/returning OGG Opus when Telegram needs voice delivery.
- Tests for no-restart `/voice set <edge-voice-id>` state updates and no cross-chat bleed.
- Manual validation steps in a test Telegram chat only after user approval.

## Common Pitfalls

1. **Confusing Groq and Grok.** Groq STT uses `GROQ_API_KEY` and Whisper-compatible models. xAI Grok STT uses xAI credentials and is a different provider.
2. **Changing global upstream defaults casually.** Ukrainian Ostap may be the user’s desired default, but not necessarily the correct global default for every Hermes install. Prefer profile config.
3. **Using config edits for live switching.** Gateway config may be cached and many config changes need restart. Runtime switching should use gateway state + session context. If source/core edits are disallowed, prefer a separate user plugin command like `/tvoice`; do not claim a plugin can override the built-in `/voice` command name.
4. **Forgetting ffmpeg.** Edge TTS output can be fine but Telegram voice delivery still fail to become a voice bubble if MP3 is not converted to Opus/OGG.
5. **Letting per-chat voice state bleed.** Never store current voice in a process-global mutable var that concurrent Telegram messages can overwrite.
6. **Testing against the real profile.** Use temporary `HERMES_HOME` for automated tests. Live Telegram tests need explicit user approval.
7. **Telegram menu cap hiding plugin commands.** Plugin slash commands can be registered and manually dispatchable while still missing from Telegram's visible `/` menu because Hermes caps `set_my_commands` output. Check plugin command registration and `telegram_menu_commands(max_commands=30)` before chasing BotFather/privacy/plugin-enable ghosts. For `telegram-tvoice`, use the plugin-only priority promotion pattern; apply the menu update with a gateway restart only when the user allows it.
8. **Footer or emoji read aloud by TTS.** Gateway runtime footers are appended after the agent's final text, so `transform_llm_output` hooks may run too early to stop them being spoken. Telegram auto-TTS does **not** rely only on `tools.tts_tool._strip_markdown_for_tts`; it calls `BasePlatformAdapter.prepare_tts_text()` and then `tools.tts_tool.text_to_speech_tool()`. For plugin-only fixes, patch/wrap both `BasePlatformAdapter.prepare_tts_text` and `tools.tts_tool.text_to_speech_tool` (optionally `_strip_markdown_for_tts` for streaming/direct paths) with a sanitizer that removes final Hermes runtime footer lines (`model · 17% · ~/cwd`) and emoji/smileys before synthesis. Keep the visible text/caption unchanged.
9. **MP3 still reaches Telegram adapter.** Even when ffmpeg/libopus exists, a caller can hand `TelegramAdapter.send_voice()` an MP3 path and Telegram will route it as `send_audio`. A plugin-only safety shim can wrap `TelegramAdapter.send_voice`, convert MP3/M4A/WAV/FLAC to OGG/Opus immediately before upload, then call the original method with the converted `.ogg` path.

## Verification Checklist

- [ ] STT provider is explicitly `groq` when Groq transcription is requested.
- [ ] Missing `GROQ_API_KEY` fails clearly and does not silently fall back to another cloud provider.
- [ ] Edge TTS uses the expected voice ID (`uk-UA-OstapNeural`, `pl-PL-MarekNeural`, etc.).
- [ ] Telegram voice replies are `.ogg` / `.opus` and delivered via `send_voice` when voice bubbles are expected.
- [ ] If a plugin shim is used, direct MP3/M4A/WAV/FLAC paths passed to Telegram `send_voice` are converted to OGG/Opus before upload.
- [ ] Spoken TTS text excludes Hermes runtime footer/status lines and emoji/smileys while preserving the visible text reply/caption.
- [ ] ffmpeg conversion is covered or missing-ffmpeg behavior is clear.
- [ ] `/voice set <edge-voice-id>` changes the next voice without gateway restart.
- [ ] Concurrent chats/topics cannot overwrite each other’s voice selection.
- [ ] No live install files under `~/.hermes/hermes-agent/**` were modified unless explicitly approved.
