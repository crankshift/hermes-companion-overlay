---
name: personality-continuity
description: Use when maintaining or using a sanitized persona, companion, cast, lore, memory index, or personality skill workspace across conversations.
license: MIT
metadata:
  version: 1.0.0
  tags: [personality, continuity, persona, memory, workspace]
  hermes:
    tags: [personality, continuity, persona, memory, workspace]
    related_skills: [personality-context-check, personality-dossier-curator, personality-reply-craft]
  created_by: agent
---

# Personality Continuity

## Overview

Use a compact workspace model for durable persona and companion continuity. Keep stable rules and pointers easy to find, while rich context stays in source files loaded only when relevant.

## Load Order

Load only what the request needs:

1. `personality/ARCHITECTURE.md` for runtime distinction, source policy, and storage rules.
2. `personality/SOUL.md` for durable identity, voice, and persona boundaries.
3. `personality/MEMORY.md` as the continuity index.
4. `personality/cast/README.md` plus a specific dossier only when recurring people or characters matter.
5. Focused topic files under `personality/lore/` only when a topic is directly relevant.
6. Personality skills only when installed or explicitly referenced.

## Storage Model

- **Core identity:** compact persona rules in `personality/SOUL.md`.
- **Index:** durable map of files in `personality/MEMORY.md`.
- **Dossiers:** recurring people or characters under `personality/cast/`.
- **Lore:** reusable voice, humor, relationship, and continuity topic files under `personality/lore/`.
- **Skills:** reusable workflows under `personality/skills/`.

Do not store secrets, raw personal dumps, exact locations, credentials, short-lived task logs, or machine-local runtime state in this workspace.

## Runtime Distinction

This directory is source material. It is not automatically active in a Hermes runtime. Before assuming a skill or identity file is installed, verify a symlink, copy, or `skills.external_dirs` mapping in the active runtime.

Do not modify a live runtime as a side effect of updating this source package unless the user explicitly asks for installation.

## Reply Workflow

1. Confirm audience and privacy context with `personality-context-check` when needed.
2. Load the narrowest relevant files.
3. Use continuity as background steering, not as text to reveal.
4. If drafting for another person, write what that person can safely see.
5. Mark uncertainty instead of inventing continuity.

## Common Pitfalls

- Loading every file by habit.
- Stuffing rich lore into the memory index.
- Turning dossiers into raw transcripts.
- Revealing that a dossier exists in an outbound message.
- Treating source files as runtime-active without verification.
- Creating one skill per person instead of using dossiers.

## Verification

- [ ] Only relevant files were loaded.
- [ ] Source versus runtime status is clear.
- [ ] Durable facts went to the right layer.
- [ ] Private details are summarized or withheld as appropriate.
- [ ] Uncertain continuity is marked as uncertain.
