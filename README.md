# Hermes Companion Overlay

Generic starter pack for a Hermes companion profile. This repository is source-only content intended to be checked out or copied to `$HOME/companion`; it is not the Hermes Agent source tree and it is not a live `$HERMES_HOME` runtime directory.

## Layout

- `AGENTS.md` - project context for sessions launched from this overlay workspace.
- `personality/` - sanitized companion personality, continuity, lore, cast, and personality-owned skill source files.
- `hermes/` - portable Hermes assets that can be linked into a real runtime profile:
  - `hermes/skills/common/` - reusable skills with no private persona dependencies.
  - `hermes/plugins/telegram-tvoice/` - portable user plugin.
- `INSTALL.md` - guarded setup commands for linking selected source assets into `$HERMES_HOME`.

## Source-Only Warning

Keep runtime state in `$HERMES_HOME`, which defaults to `$HOME/.hermes`. Do not store secrets, sessions, logs, databases, caches, generated profile data, or Hermes built-in memories in this repository.

Runtime activation is deliberate:

- `personality/SOUL.md` becomes active only when linked or copied to `$HERMES_HOME/SOUL.md`.
- `personality/MEMORY.md` stays a source index and must not be linked into `$HERMES_HOME/memories/`.
- Skills and plugins are discovered only after explicit runtime mapping.

See `INSTALL.md` for guarded setup commands that refuse to overwrite existing runtime files or directories.
