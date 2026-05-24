# Personality Continuity Architecture

This directory is a generic personality continuity workspace managed from this repository. It is for durable persona, companion-continuity, cast, lore, and future personality-owned skill source files that are not tied to any private project identity.

It is a source workspace, not a live Hermes runtime home.

## Runtime distinction

- `personality/SOUL.md` is a durable generic identity/persona source file.
- `personality/SOUL.md` is not runtime-active unless explicitly copied or linked to `$HERMES_HOME/SOUL.md`.
- `personality/MEMORY.md` is a compact continuity index, not Hermes built-in persistent memory under `$HERMES_HOME/memories/`.
- `personality/skills/` stores generic personality-specific skill source. Runtime discovery requires an explicit symlink, copy, or `skills.external_dirs` mapping.

## Load order

When a session needs generic personality or companion-continuity context, load only what is relevant:

1. `personality/ARCHITECTURE.md`
2. `personality/SOUL.md` for durable identity, voice, and persona boundaries
3. `personality/MEMORY.md` as the continuity index
4. `personality/cast/README.md` when recurring people, characters, or dossiers matter
5. Topic files under `personality/lore/` only when needed
6. Personality-specific skills under `personality/skills/` only when installed or explicitly referenced

Do not load every file by default. The workspace is meant to stay compact, reusable, and easy to audit.

## Skill catalog

- `personality-context-check` - privacy, audience, seriousness, uncertainty, and humor-dose guardrail.
- `personality-reply-craft` - warm, direct, non-corporate replies, roasts, and social message drafts.
- `personality-ai-banter` - companion-to-companion and bot-to-bot banter with privacy-safe technical metaphors.
- `personality-continuity` - workflow for using this source workspace without loading everything.
- `personality-dossier-curator` - creation and maintenance of sanitized recurring-person or character dossiers.

## Storage rules

- Store generic identity/persona notes in `personality/SOUL.md`.
- Store the continuity map in `personality/MEMORY.md`.
- Store recurring people, characters, and relationship dossiers in `personality/cast/`.
- Store reusable style, vocabulary, humor, relationship, or continuity topic notes in `personality/lore/`.
- Store personality-specific skill source under `personality/skills/`.
- Keep short-lived task progress, logs, generated artifacts, secrets, credentials, and machine-local runtime state outside this workspace.

## Boundaries

This workspace must stay sanitized and independent. Do not import private cast notes, raw personal notes, exact locations, credentials, tokens, or project-specific lore unless the user explicitly asks for a deliberate, sanitized migration.

If a fact is uncertain, mark it as uncertain or say that it is unknown. Do not fill continuity gaps with invented history.

## Source-only runtime runbook

These commands are examples for a deliberate install step. Do not run them as part of ordinary source edits.

Verify the source package:

```bash
find personality/skills -name SKILL.md -print
```

Symlink into a Hermes runtime, when explicitly requested:

```bash
mkdir -p "$HERMES_HOME/skills"
ln -sfn "<repo-root>/personality/skills" "$HERMES_HOME/skills/personality"
```

Copy instead of symlink, when the runtime should be self-contained:

```bash
mkdir -p "$HERMES_HOME/skills/personality"
cp -R "<repo-root>/personality/skills/." "$HERMES_HOME/skills/personality/"
```

If the runtime supports external skill directories, prefer a `skills.external_dirs` entry that points at `<repo-root>/personality/skills` and verify discovery in that runtime before relying on the commands.
