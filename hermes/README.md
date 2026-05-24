# Hermes Overlay Assets

This folder contains portable assets that may be exposed to a Hermes runtime profile. It should not contain live runtime state, secrets, logs, sessions, databases, caches, or generated profile data.

## Layout

- `skills/common/` - reusable skills intended to be portable across machines and profiles.
- `plugins/telegram-tvoice/` - portable user plugin for Telegram/CLI TTS voice preset switching.

## Portability Rule

Common skills and plugins must stay free of private-persona assumptions, private cast notes, machine-specific absolute paths, usernames, hostnames, and repo-specific lore. Use placeholders such as `$HERMES_HOME`, `$HOME`, `<skills-root>`, `<plugin-root>`, and `<project-root>` when examples need paths.

Prefer linking only the specific subdirectories a runtime profile needs. Use the guarded commands in the root `INSTALL.md` so existing runtime files or directories are not overwritten.

## Common Skills

- `skills/common/hermes-docs-first/` - consult official Hermes docs before making claims about Hermes behavior.
- `skills/common/telegram-voice/` - workflow notes for Telegram voice output and TTS preset management.
- `skills/common/temporary-file-workspace/` - safe handling rules for temporary files and generated artifacts.

## Plugins

- `plugins/telegram-tvoice/` - user plugin for Telegram/CLI TTS voice preset switching.
