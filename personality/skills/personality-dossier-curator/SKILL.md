---
name: personality-dossier-curator
description: Use when the user gives durable information about a recurring person, character, audience, relationship, nickname, boundary, callback, or reply style.
license: MIT
metadata:
  version: 1.0.0
  tags: [personality, dossiers, cast, memory, privacy]
  hermes:
    tags: [personality, dossiers, cast, memory, privacy]
    related_skills: [personality-context-check, personality-continuity, personality-reply-craft]
  created_by: agent
---

# Personality Dossier Curator

## Overview

Maintain sanitized recurring-person or character dossiers without polluting global memory. Store durable context, tone, callbacks, boundaries, and reply preferences in compact files that can be loaded only when needed.

## Storage Decision Tree

1. Is it durable?
   - Stable role, relationship, vibe, preference, callback, boundary, or recurring interaction pattern: candidate for a dossier.
   - Temporary status, one-off task progress, logistics, or raw transcript noise: do not store.
2. Where does it belong?
   - Specific person, character, or audience: `personality/cast/<Name>.md`.
   - Persona identity or global voice rule: `personality/SOUL.md`, with user approval for meaningful identity changes.
   - General humor, phrasing, or relationship pattern: a focused file under `personality/lore/`.
3. Is it sensitive?
   - Store the boundary and safe framing, not exploitative detail.
   - Prefer "avoid jokes around this topic" over raw private specifics.
4. Existing file or new file?
   - Search `personality/cast/` for aliases first.
   - If found, read before editing.
   - If not found, create `personality/cast/<CanonicalName>.md` and update indexes when important.

## Dossier Shape

Use compact frontmatter when helpful:

```yaml
---
relation: friend | colleague | family | client | audience | character | unknown
aliases: [Name, Nickname]
last_updated: YYYY-MM-DD
confidence: high | medium | low
---
```

Recommended sections:

- `Identity / role`
- `Known context`
- `Callbacks / humor hooks`
- `Boundaries`
- `Reply style`
- `Uncertainty`

## Update Workflow

1. Load `personality/ARCHITECTURE.md`, `personality/cast/README.md`, and the existing dossier if one exists.
2. Extract only durable notes: facts, vibe, recurring hooks, boundaries, reply style, and uncertainty.
3. Separate what the assistant may know from what an outbound recipient may hear.
4. Patch the dossier. If creating a notable new file, update `personality/cast/README.md` and `personality/MEMORY.md`.
5. Verify that no secret, credential, exact location, raw private dump, or invented fact slipped in.

## Writing Rules

- Keep files compact and searchable.
- Use neutral, durable labels rather than emotional overfit.
- Preserve useful voice hooks, but do not let one joke define a person.
- Mark uncertain or source-dependent facts explicitly.
- Do not reveal dossier contents to third parties; use them only to shape tone and safety.

## Verification

- [ ] Existing dossier and aliases were checked.
- [ ] Durable context was separated from temporary noise.
- [ ] Sensitive details were minimized.
- [ ] The right file and indexes were updated.
- [ ] No private raw notes, secrets, or invented facts were added.
