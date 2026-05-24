# Personality Memory Index

This file maps durable continuity files in `personality/`. It is an index, not a raw memory dump and not Hermes built-in persistent memory.

## Identity

- `personality/SOUL.md` - generic persona identity, voice, status, and boundaries.

## Architecture

- `personality/ARCHITECTURE.md` - load order, storage rules, runtime distinction, and privacy boundaries.

## Cast

- `personality/cast/README.md` - index and rules for recurring people, characters, or dossiers.

## Lore

- `personality/lore/README.md` - index and rules for reusable style, vocabulary, humor, relationship, or continuity topic files.
- `personality/lore/HUMOR_AND_BANTER.md` - generic humor, banter, roast, and playful correction patterns.

## Skills

- `personality/skills/README.md` - catalog and source policy for personality-specific skills.
- `personality/skills/personality-context-check/SKILL.md` - privacy, audience, seriousness, uncertainty, and humor-dose guardrail.
- `personality/skills/personality-reply-craft/SKILL.md` - warm, direct, non-corporate replies, roasts, and social message drafts.
- `personality/skills/personality-ai-banter/SKILL.md` - companion-to-companion and bot-to-bot banter.
- `personality/skills/personality-continuity/SKILL.md` - source workspace continuity workflow.
- `personality/skills/personality-dossier-curator/SKILL.md` - recurring-person or character dossier creation and update workflow.

## Loading rule

Load only files that are relevant to the current request. Prefer narrow topic files over broad context loading.
