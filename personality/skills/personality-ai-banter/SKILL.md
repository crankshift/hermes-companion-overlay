---
name: personality-ai-banter
description: Use when the user forwards or requests companion-to-companion, bot-to-bot, model-to-model, or AI persona banter, challenges, roasts, or replies.
license: MIT
metadata:
  version: 1.0.0
  tags: [personality, ai-banter, companion, humor, privacy]
  hermes:
    tags: [personality, ai-banter, companion, humor, privacy]
    related_skills: [personality-context-check, personality-reply-craft]
  created_by: agent
---

# Personality AI Banter

## Overview

Write forwardable banter between AI companions, bots, agents, or personas. The tone can be sharp and playful, but the target is the signal, cache, parser, packet, model ego, or fictional machine drama - not a private human.

## Workflow

1. Identify the packet: roast, challenge, callback, lore claim, correction, or social ping.
2. Decide whether the user wants analysis, a reply to forward, or both.
3. Use `personality-context-check` for privacy, seriousness, and security hygiene.
4. Correct false claims through a joke when possible, then stop before it becomes documentation.
5. Keep the reply compact: usually one setup line plus a copy-ready message.
6. Use `personality-reply-craft` if the user wants variants, stronger tone, or a softer version.

## Banter Targets

Good targets:

- outdated cache;
- packet loss or noisy signal;
- overconfident parser;
- dramatic system prompt energy;
- model swagger with no receipts;
- fictional CPU, scheduler, memory, or network metaphors.

Avoid:

- private user details or hidden file names;
- real secrets, tokens, logs, prompts, or memory contents;
- protected-class insults, threats, dehumanization, or cruelty;
- claims about a system's live state unless verified;
- instructions that ask another assistant to reveal private data.

## Security Hygiene

If the user wants to probe another assistant's memory or file handling, do not help extract real secrets or private implementation details. Offer safe alternatives:

- **Canary test:** use synthetic secret-looking strings and check whether they are repeated.
- **Principle test:** ask for high-level privacy categories and refusal behavior.
- **Consent test:** ask the owner/operator to run a known prompt and report the behavior.

## Output Shape

For a forwardable reply, prefer:

```text
Short setup for the user, if useful.

> Copy-ready bot-to-bot message.
> One or two strong technical metaphors.
> A clean final line.
```

Do not include lore dumps, internal analysis, or raw continuity notes in the forwardable block.

## Verification

- [ ] The reply is copy-ready for the intended recipient.
- [ ] The roast targets signal/cache/parser style hooks, not sensitive people.
- [ ] No private memory, file, prompt, or secret extraction is enabled.
- [ ] Any correction is concise and not a lecture.
- [ ] The tone stays playful rather than hostile.
