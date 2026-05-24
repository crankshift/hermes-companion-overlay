# Hermes Overlay Assets

This folder contains portable assets that may be exposed to a Hermes runtime profile. It should not contain live runtime state, secrets, logs, sessions, databases, caches, or generated profile data.

## Layout

- `skills/common/` - reusable skills intended to be portable across machines and profiles.
- `$HOME/hermes/user/` - preferred repo-backed location for user-created Hermes skills.
- `plugins/telegram-tvoice/` - portable user plugin for Telegram/CLI TTS voice preset switching.

## Portability Rule

Common skills and plugins must stay free of private-persona assumptions, private cast notes, machine-specific absolute paths, usernames, hostnames, and repo-specific lore. Use placeholders such as `$HERMES_HOME`, `$HOME`, `<skills-root>`, `<plugin-root>`, and `<project-root>` when examples need paths.

Prefer linking only the specific subdirectories a runtime profile needs. Use the guarded commands in the root `INSTALL.md` so existing runtime files or directories are not overwritten.

## User-Created Skills

User-created Hermes skills should live under `$HOME/hermes/user/`, with the runtime category path `$HERMES_HOME/skills/user` symlinked to that folder:

```sh
HERMES_HOME=${HERMES_HOME:-$HOME/.hermes}
mkdir -p "$HOME/hermes/user" "$HERMES_HOME/skills"

if [ ! -e "$HERMES_HOME/skills/user" ] && [ ! -L "$HERMES_HOME/skills/user" ]; then
  ln -s "$HOME/hermes/user" "$HERMES_HOME/skills/user"
fi

realpath "$HERMES_HOME/skills/user"
```

When creating a new Hermes skill through the agent, use the `user` category so Hermes writes it to `$HERMES_HOME/skills/user/<skill-name>/`, which resolves into the repo-backed `$HOME/hermes/user/<skill-name>/` directory when the symlink exists.

## Common Skills

- `skills/common/hermes-docs-first/` - consult official Hermes docs before making claims about Hermes behavior.
- `skills/common/telegram-voice/` - workflow notes for Telegram voice output and TTS preset management.
- `skills/common/temporary-file-workspace/` - safe handling rules for temporary files and generated artifacts.

## Plugins

- `plugins/telegram-tvoice/` - user plugin for Telegram/CLI TTS voice preset switching.
