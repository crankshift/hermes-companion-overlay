# Install Hermes Companion Overlay

These commands link selected source assets from `$HOME/companion` into a live Hermes runtime. They are intentionally guarded: existing runtime files or directories are not replaced.

## Clone Location

The examples below assume this overlay is checked out at `$HOME/companion`, even if the Git repository is named `hermes-companion-overlay`. Clone with an explicit destination so the local folder matches the default install path:

```bash
git clone <repo-url> "$HOME/companion"
cd "$HOME/companion"
```

If you keep the checkout somewhere else, set `OVERLAY_HOME` to that path before running the install commands:

```bash
export OVERLAY_HOME=/path/to/hermes-companion-overlay
```

## Defaults

- `OVERLAY_HOME` defaults to `$HOME/companion`.
- `HERMES_HOME` defaults to `$HOME/.hermes`.
- The overlay remains source-only. Runtime config, secrets, sessions, logs, memories, skills, plugins, and caches stay under `$HERMES_HOME`.

## Before Installing

Update `personality/SOUL.md` with the desired companion personality before linking it into the runtime. This file is the main source Hermes uses for persona, voice, role, boundaries, and interaction style once it is active as `$HERMES_HOME/SOUL.md`.

## Guarded Symlink Install

Review the script before running it in your shell:

```bash
set -eu

OVERLAY_HOME=${OVERLAY_HOME:-$HOME/companion}
HERMES_HOME=${HERMES_HOME:-$HOME/.hermes}

if [ ! -f "$OVERLAY_HOME/AGENTS.md" ]; then
  echo "Refusing to install: $OVERLAY_HOME/AGENTS.md was not found." >&2
  exit 1
fi

OVERLAY_HOME=$(cd "$OVERLAY_HOME" && pwd -P)
mkdir -p "$HERMES_HOME"
HERMES_HOME=$(cd "$HERMES_HOME" && pwd -P)

require_path() {
  if [ ! -e "$1" ]; then
    echo "Refusing to install: required source path is missing: $1" >&2
    exit 1
  fi
}

link_path_once() {
  src=$1
  dst=$2

  require_path "$src"
  mkdir -p "$(dirname "$dst")"

  if [ -L "$dst" ]; then
    current=$(readlink "$dst")
    if [ "$current" = "$src" ]; then
      echo "Already linked: $dst -> $src"
      return 0
    fi
    echo "Refusing to replace existing symlink: $dst -> $current" >&2
    exit 1
  fi

  if [ -e "$dst" ]; then
    echo "Refusing to replace existing runtime path: $dst" >&2
    exit 1
  fi

  ln -s "$src" "$dst"
  echo "Linked: $dst -> $src"
}

require_path "$OVERLAY_HOME/personality/SOUL.md"
require_path "$OVERLAY_HOME/personality/skills"
require_path "$OVERLAY_HOME/hermes/skills/common"
require_path "$OVERLAY_HOME/hermes/plugins/telegram-tvoice"

link_path_once "$OVERLAY_HOME/personality/SOUL.md" "$HERMES_HOME/SOUL.md"
link_path_once "$OVERLAY_HOME/personality/skills" "$HERMES_HOME/skills/personality"

if [ -L "$HERMES_HOME/skills/common" ]; then
  echo "Refusing to install common skills: $HERMES_HOME/skills/common is a symlink." >&2
  echo "Create a real directory there first so individual skills can be linked safely." >&2
  exit 1
fi

mkdir -p "$HERMES_HOME/skills/common"

for skill_dir in "$OVERLAY_HOME"/hermes/skills/common/*; do
  [ -d "$skill_dir" ] || continue
  link_path_once "$skill_dir" "$HERMES_HOME/skills/common/$(basename "$skill_dir")"
done

link_path_once "$OVERLAY_HOME/hermes/plugins/telegram-tvoice" "$HERMES_HOME/plugins/telegram-tvoice"
```

## Gateway Sessions

To make gateway-launched sessions discover this overlay as project context, set:

```bash
export MESSAGING_CWD=${MESSAGING_CWD:-$OVERLAY_HOME}
```

Use the absolute overlay path if this is set outside the install shell:

```bash
export MESSAGING_CWD=$HOME/companion
```

## Verification

After installing into a runtime, inspect the links before relying on them:

```bash
ls -l "$HERMES_HOME/SOUL.md"
ls -l "$HERMES_HOME/skills/personality"
ls -l "$HERMES_HOME/skills/common"
ls -l "$HERMES_HOME/plugins/telegram-tvoice"
```

`personality/MEMORY.md` is intentionally not linked into `$HERMES_HOME/memories/`.
