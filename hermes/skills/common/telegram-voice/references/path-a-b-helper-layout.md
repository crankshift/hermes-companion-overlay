# Path A+B Helper Layout for Telegram Voice

Session-derived note for safe Hermes Telegram voice customization without source edits.

## Durable lesson

Do not put personal voice helper scripts under the live Hermes source tree, including hypothetical paths like:

- `~/.hermes/hermes-agent/tools/_user/`
- `~/.hermes/hermes-agent/tools/_custom/`
- `~/.hermes/hermes-agent/tools/custom/`
- `~/.hermes/hermes-agent/tools/user/`

Those paths are not the right extension surface for a personal helper. They are inside the installed Hermes source tree and can create update conflicts or accidental core-tool import/registry expectations.

## Preferred portable layout

Prefer plugin-only, with no helper folder under `~/.hermes/scripts/`. Use Hermes' documented user plugin root by default:

```text
~/.hermes/plugins/telegram-tvoice/
├── plugin.yaml
├── __init__.py
└── INSTALL.md
```

If the user keeps plugins in a dotfiles repo or shared project repo, discover that local convention first and use placeholders in docs:

```text
<plugin-repo>/telegram-tvoice/
~/.hermes/plugins -> <plugin-repo>        # optional whole-root symlink
```

This keeps the customization source-free, update-safe, Hermes-native, Git-trackable when a repo is used, and easy to remove. Do not bake one user's repo name or absolute home path into reusable/common docs.

## Legacy shell-helper layout

Only use a shell helper if the user explicitly asks for a non-Hermes shell command. If a helper is temporary, remove it when the plugin replaces it, including any `~/.local/bin/voice-preset` or `~/.local/bin/tvoice` symlinks that point to the deleted helper.

A plugin can register a command name distinct from built-in `/voice`. Do not try to override `/voice` from a plugin; built-in command names win.

## Known limitations of Path A+B

- It changes profile-level config such as `tts.edge.voice`, not gateway-owned per-chat runtime state.
- It may work for next TTS generation because `tools/tts_tool.py` reads config on each call and config caching keys off file mtime/size.
- If the running gateway has not picked up `.env` changes or does not reload the relevant config before TTS generation, use `/restart` once.
- True per-chat no-restart voice switching still requires Hermes core support via gateway state plus `gateway.session_context`.

## Example helper commands

```bash
voice-preset status
voice-preset ua-ostap
voice-preset pl-marek
voice-preset auto "Привіт, говоримо українською"
echo "Cześć, mówimy po polsku" | voice-preset auto

# Short alias if installed:
tvoice status
tvoice pl-marek
```
