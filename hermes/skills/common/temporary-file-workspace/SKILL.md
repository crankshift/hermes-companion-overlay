---
name: temporary-file-workspace
description: Use when processing user-supplied files, archives, exports, or document dumps temporarily; keep scratch work isolated and clean it up after durable outputs are written.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [temporary-files, downloads, archives, cleanup, workspace]
  created_by: agent
---

# Temporary File Workspace

## Overview

Handle temporary user-supplied files in a predictable scratch area instead of scattering them through home folders or project directories. Keep durable outputs in the intended project/workspace and remove scratch data when the task is complete.

## When to Use

Use this skill when:

- the user sends a file, archive, document export, log bundle, or ZIP/TAR/7z dump;
- files need to be unpacked, inspected, converted, summarized, imported, or transformed;
- the user says the files are temporary or should be deleted after processing;
- work needs scratch space that should not pollute the project repository.

## Workflow

1. Pick or create a task-specific scratch directory.
2. Copy/save the incoming file there, preserving the original name when possible.
3. For archives, inspect contents before extraction when possible:

   ```bash
   unzip -l archive.zip
   tar -tf archive.tar
   ```

4. Extract into a task subfolder.
5. Build a manifest of relevant files.
6. Read/process every requested file fully, or explicitly skip with a reason.
7. Write durable outputs only to the intended project/workspace location.
8. Delete scratch files after completion unless the user explicitly asks to keep them.
9. Report what was processed, what durable files changed, and whether scratch files were removed.

## Safety

- Do not delete outside the task-specific scratch directory.
- Do not silently drop files from an import.
- Do not store secrets, raw private dumps, or temporary artifacts in durable project files unless the user explicitly requests it and it is safe.
- Preserve uncertainty and provenance when importing notes from old exports.

## Verification Checklist

- [ ] Scratch directory was task-specific.
- [ ] Archive contents were listed before or during extraction.
- [ ] Every requested file was fully read or explicitly skipped with reason.
- [ ] Durable outputs were written to the intended workspace.
- [ ] Scratch files were removed after completion unless the user asked to keep them.
- [ ] Final response names created/updated durable files and cleanup status.
