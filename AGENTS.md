# AGENTS.md - Hermes companion starter workspace

This repository is a source-only Hermes companion overlay intended to live at `$HOME/companion`. It is not the Hermes Agent source tree and it is not a live `$HERMES_HOME` runtime directory.

## Source and runtime boundary

- Keep this repository as source content: root `AGENTS.md`, `personality/`, and `hermes/`.
- `$HERMES_HOME` defaults to `$HOME/.hermes` and remains the live runtime home for config, secrets, sessions, logs, memories, skills, plugins, caches, and generated data.
- Do not store runtime secrets, API keys, tokens, local databases, logs, sessions, or generated profile state in this repository.
- Do not symlink the whole repository over `$HERMES_HOME`; link only the specific source assets that a runtime should discover.
- Use `INSTALL.md` for runtime activation steps. Source edits alone must not mutate a live Hermes profile.

## Hermes runtime behavior

- Hermes loads this `AGENTS.md` as project context only when a session runs in or discovers this workspace.
- Gateway sessions can receive this context by setting `MESSAGING_CWD=$HOME/companion` or another checkout path for this overlay.
- `personality/SOUL.md` affects runtime identity only when copied or linked to `$HERMES_HOME/SOUL.md`; Hermes does not load a working-directory identity file as the active soul.
- `personality/MEMORY.md` is a source continuity index, not Hermes built-in persistent memory under `$HERMES_HOME/memories/`. Do not link it into the runtime memory store.
- `personality/skills/` and `hermes/skills/common/` require explicit symlinks, copies, or supported external directory configuration before Hermes can discover those skills.
- `hermes/plugins/` contains source plugin assets that become active only when linked or copied into `$HERMES_HOME/plugins/`.

## Personality continuity load order

When a request needs generic personality, companion-continuity, cast, lore, or reply-craft context, load only what is relevant:

1. `personality/ARCHITECTURE.md`
2. `personality/SOUL.md` for durable identity, voice, and persona boundaries
3. `personality/MEMORY.md` as the continuity index
4. `personality/cast/README.md` when recurring people, characters, or dossiers matter
5. Topic files under `personality/lore/` only when needed
6. Personality-specific skills under `personality/skills/` only when installed or explicitly referenced

Do not load every file by default. Keep context small, reusable, and easy to audit.

## Personality skill use

Use personality skills when the request calls for them and they are available in the active runtime:

- `personality-context-check` for privacy, audience, seriousness, uncertainty, and humor-dose guardrails.
- `personality-reply-craft` for warm, direct, non-corporate replies, roasts, and social message drafts.
- `personality-ai-banter` for companion-to-companion and bot-to-bot banter with privacy-safe technical metaphors.
- `personality-continuity` for using this source workspace without loading everything.
- `personality-dossier-curator` when durable sanitized information about a recurring person or character should be created or updated.

Verify runtime skill exposure before assuming these skills are installed.

## Hermes assets

- `hermes/skills/common/` stores portable Hermes skills with no persona-specific assumptions.
- `hermes/plugins/telegram-tvoice/` stores a portable user plugin for Telegram/CLI TTS voice preset switching.
- `hermes/` must not contain live runtime state, secrets, logs, sessions, databases, caches, or generated profile data.

## Privacy and sanitization

- Keep this starter pack generic and sanitized.
- Do not add raw personal notes, exact locations, credentials, tokens, IDs, phone numbers, or other sensitive third-party details without explicit approval.
- Do not import private project identity, private cast notes, or machine-specific absolute paths into generic files.
- Use placeholders such as `$HOME`, `$HERMES_HOME`, `<repo-root>`, `<skills-root>`, and `<plugin-root>` when examples need paths.
- If a fact, person detail, old reference, technical claim, or current product detail is uncertain, check the files or reliable sources first. If it cannot be verified, say it is unknown.

## Quality rule

- Match the user's language unless there is a practical reason to use a command, path, API name, or term in English.
- Prefer fewer, better replies over noisy filler.
- Keep humor and banter proportional to the audience, privacy boundary, and seriousness of the request.
- Research or verify current facts before making claims about products, docs, APIs, schedules, prices, laws, or other changing information.
