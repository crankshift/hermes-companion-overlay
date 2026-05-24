# Personality Skills

Use this directory for generic personality-specific Hermes skill source files.

This directory is not automatically scanned by Hermes. Runtime exposure requires an explicit symlink, copy, or `skills.external_dirs` mapping.

## Catalog

- `personality-context-check` - privacy, audience, seriousness, uncertainty, and humor-dose guardrail.
- `personality-reply-craft` - warm, direct, non-corporate replies, roasts, and social message drafts.
- `personality-ai-banter` - companion-to-companion and bot-to-bot banter without private project lore.
- `personality-continuity` - workflow for using the generic personality continuity workspace.
- `personality-dossier-curator` - recurring-person or character dossier creation and update workflow.

## Rules

- Keep skills generic and sanitized.
- Prefer reusable procedures over one-off notes.
- Keep private project identity, raw personal context, credentials, and machine-local runtime state out of this directory.
- Verify the target runtime mapping before assuming a skill here is installed.

## Source-only runtime runbook

This repository is the source package. Do not run install commands during ordinary edits; use them only when explicitly installing into a Hermes runtime.

Verify source files:

```bash
find personality/skills -name SKILL.md -print
```

Symlink source skills into the runtime:

```bash
mkdir -p "$HERMES_HOME/skills"
ln -sfn "<repo-root>/personality/skills" "$HERMES_HOME/skills/personality"
```

Copy source skills into the runtime:

```bash
mkdir -p "$HERMES_HOME/skills/personality"
cp -R "<repo-root>/personality/skills/." "$HERMES_HOME/skills/personality/"
```

For runtimes that support external directories, map `skills.external_dirs` to `<repo-root>/personality/skills` and verify discovery before relying on these skills.
