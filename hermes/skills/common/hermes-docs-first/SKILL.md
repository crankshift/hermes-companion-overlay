---
name: hermes-docs-first
description: >-
  Use whenever a user asks to configure, set up, troubleshoot, modify, extend,
  plan, or implement anything in Hermes Agent. This skill enforces a docs-first
  workflow: before making a plan or code/config change, read the upstream
  Hermes docs under https://github.com/NousResearch/hermes-agent/tree/main/website/docs
  and cite what was checked. Also use this when creating, updating, moving, or
  organizing reusable skills/plugins: common assets must stay portable and local
  canonical paths must be discovered from the current machine/config rather than
  hardcoded. Use this especially when a Hermes change could tempt edits to
  active core, gateway, toolset, provider, or installed source files: default to
  overlay/customization layers and protect live installs.
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, documentation, skills, plugins, workflow]
    homepage: https://github.com/NousResearch/hermes-agent/tree/main/website/docs
    related_skills: [hermes-agent, skill-creator]
  created_by: agent
---

# Hermes Docs First

## Purpose

Use this skill as a guardrail for Hermes Agent work. Hermes-related tasks should be grounded in the actual Hermes documentation before planning or implementation. Reusable skills and plugins should stay portable across machines and agents.

Core rule: docs first, plan second, implementation third. No cargo-culting from memory, no confident hallucinated config keys, no raccoon-with-root-access speedrun into a live install tree.

Core-protected rule: Hermes changes are overlay-first by default. Active Hermes core/install files are for inspection and diagnosis, not mutation.

## Trigger conditions

Load this skill whenever the user asks about Hermes Agent itself, including:

- configuring, installing, updating, enabling/disabling, or troubleshooting Hermes;
- changing CLI behavior, slash commands, toolsets, gateway, Telegram/Discord/voice, providers, models, profiles, cron, MCP, plugins, memory, sessions, skills, or curator behavior;
- changing behavior that might otherwise seem to require editing core, gateway, toolset, provider, or installed source files;
- editing or planning changes to Hermes source code, docs, config, plugins, or workflows;
- creating, updating, moving, organizing, or publishing reusable skills/plugins.

If the task is both Hermes-related and code-related, also load/use the relevant development skill after this docs-first pass.

## Mandatory docs-first workflow

Before producing a plan, commands, config edits, code edits, or a design for Hermes work:

1. Load the existing `hermes-agent` skill if it is not already loaded.
2. Read relevant upstream docs from the Hermes docs tree:
   - Primary docs root: `https://github.com/NousResearch/hermes-agent/tree/main/website/docs`
   - Prefer the public docs site pages when they are easier to extract: `https://hermes-agent.nousresearch.com/docs/`
   - If working inside a safe local checkout/worktree, read the matching files under `website/docs/` with `read_file`/`search_files`.
3. Pick docs pages based on the task area. Examples:
   - tools/toolsets -> tools reference and configuration docs;
   - gateway/Telegram/voice -> messaging docs plus voice/STT/TTS docs;
   - providers/models -> providers docs and configuration docs;
   - skills/curator -> skills catalog/skills docs and curator docs;
   - plugins -> plugin feature docs and the build-a-plugin guide;
   - cron/webhooks/MCP/profiles -> the matching feature docs.
4. State the docs evidence before the plan, using a short line like:
   `Docs checked: <page/file 1>, <page/file 2>.`
5. Classify the requested change before planning:
   - User customization/extension -> implement it as an overlay layer.
   - Reusable capability -> implement it as a skill, skill bundle, or plugin, not as a core patch.
   - Missing upstream capability -> say core support is needed, then plan safe upstream checkout/worktree work only if the user explicitly asks to contribute upstream.
6. Only then create the plan or implement the change.

If the docs cannot be fetched or found, say so explicitly and either retry with another route (`web_search`, docs site, GitHub raw file, local checkout) or ask the user whether to proceed with an assumption. Do not pretend the docs were checked.

## Overlay-first, core-protected discipline

Default to supported overlay/customization layers for every Hermes change. The chosen implementation must survive `hermes update`; if an update would overwrite the change, it is not an acceptable default plan.

Do not edit active Hermes install/source files, including:

- `$HERMES_HOME/hermes-agent/**`;
- `~/.hermes/hermes-agent/**`;
- site-packages installs such as `site-packages/hermes_agent/**`;
- active gateway, core, toolset, provider, or runtime-owned files;
- any other discovered live install path.

Read and inspect those files only for diagnosis. If behavior cannot be changed through an overlay layer, state that upstream/core support appears to be required and stop short of live-install surgery unless the user explicitly asks for upstream contribution work in a safe checkout/worktree.

Prefer supported, update-resilient layers:

- config/profile/env changes documented by Hermes;
- skills and skill bundles;
- user plugins under `~/.hermes/plugins/`;
- project plugins under `.hermes/plugins/` when explicitly enabled by the project;
- pip-installed plugins;
- external skill dirs configured through `skills.external_dirs`;
- wrappers, runbooks, launch scripts, or repo-backed symlinks that leave live install files untouched.

When the user explicitly asks to contribute upstream core support, use a non-live checkout/worktree or a user-approved source repository. Never treat the active installed Hermes tree as the development workspace.

If another Hermes skill or local note suggests live-install surgery for a narrower area, this overlay-first, core-protected rule wins unless the user explicitly asks for upstream contribution work in a safe checkout/worktree.

## Portable common-asset discipline

Common skills and reusable plugins may be copied to other machines or agents. Keep them free of machine-specific assumptions:

- Do not hardcode usernames, hostnames, private repo names, absolute home paths, or one user's conventions inside common skill/plugin content.
- Use placeholders such as `<skills-root>`, `<plugin-root>`, `<project-root>`, `$HOME`, `$HERMES_HOME`, and `~/.hermes` when examples need paths.
- Discover actual local paths with tools before editing, for example:
  - `realpath ~/.hermes/skills/<category>` for a skill category;
  - `realpath ~/.hermes/plugins` for the active user plugin root;
  - `hermes config path` and `hermes config env-path` for config/env files.
- If the current machine has a local canonical repo layout, keep those specifics in local architecture notes, memory, or deployment docs — not in common skills/plugins intended for reuse elsewhere.
- When writing install docs, show direct `~/.hermes/...` installation first, then describe optional repo/symlink layouts with placeholders.

## Plan/implementation template

For Hermes tasks, structure the first substantive response like this:

```text
Docs checked: <doc URL/file>, <doc URL/file>
What the docs imply: <1-3 bullets>
Plan: <short, ordered steps>
```

Then execute the plan with tools. Keep working until the change is verified.

## Verification checklist

Before finalizing a Hermes-related task, confirm:

- [ ] Relevant Hermes docs were actually read before planning/implementation.
- [ ] The answer or plan cites the checked docs/pages/files.
- [ ] Any config key, command, or path came from docs, local files, or live tool output.
- [ ] The request was classified before planning as customization/extension, reusable capability, or missing upstream capability.
- [ ] No active Hermes install/source file was edited; live install files were inspected only for diagnosis.
- [ ] The implementation is update-resilient and should survive `hermes update`.
- [ ] Common skills/plugins contain no hardcoded user-specific, home-directory, or private-repo paths.
- [ ] Any machine-specific canonical path was documented only in local notes or memory, not inside portable common assets.
