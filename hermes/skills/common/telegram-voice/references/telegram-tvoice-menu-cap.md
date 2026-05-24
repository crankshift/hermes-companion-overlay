# Telegram `/tvoice` plugin menu cap troubleshooting

Session-derived detail for the `telegram-tvoice` user plugin.

## Symptom

`telegram-tvoice` is installed and enabled, but Telegram's `/` command menu does not show `/tvoice`.

## Root cause pattern

Hermes can register plugin slash commands correctly while still hiding them from Telegram's visible BotCommand menu:

- `ctx.register_command("tvoice", ...)` registers the plugin command.
- `hermes plugins list` can show `telegram-tvoice` as enabled.
- `get_plugin_commands()` can include `tvoice` and manual `/tvoice status` may dispatch.
- Telegram BotCommand menu is capped by Hermes to a small visible list (`telegram_menu_commands(max_commands=30)` in the observed build), so plugin commands can be pushed beyond the cap by built-in commands.

This is not a missing plugin, not necessarily a BotFather issue, and not a reason to edit live Hermes core.

## Diagnosis commands

Run with Hermes' own venv when available so imports match the gateway install:

```bash
python - <<'PY'
from hermes_cli.plugins import get_plugin_commands, get_plugin_command_handler
from hermes_cli.commands import telegram_bot_commands, telegram_menu_commands

cmds = get_plugin_commands()
menu, hidden = telegram_menu_commands(max_commands=30)
names = [n for n, _ in menu]
print('plugin_commands=', sorted(cmds.keys()))
print('tvoice_handler=', bool(get_plugin_command_handler('tvoice')))
print('tvoice_in_bot_commands=', 'tvoice' in {n for n, _ in telegram_bot_commands()})
print('tvoice_in_menu=', 'tvoice' in names)
print('tvoice_index=', names.index('tvoice') if 'tvoice' in names else None)
print('hidden=', hidden)
print('menu=', names)
PY
```

To check what Telegram currently has, use Bot API through python-telegram-bot and `TELEGRAM_BOT_TOKEN` from Hermes config/env:

```bash
python - <<'PY'
import asyncio
from hermes_cli.config import get_env_value
from telegram import Bot, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats

async def main():
    token = get_env_value('TELEGRAM_BOT_TOKEN')
    bot = Bot(token)
    for scope in [BotCommandScopeDefault(), BotCommandScopeAllPrivateChats(), BotCommandScopeAllGroupChats()]:
        cmds = await bot.get_my_commands(scope=scope)
        names = [c.command for c in cmds]
        print(type(scope).__name__, 'count=', len(names), 'has_tvoice=', 'tvoice' in names, names)

asyncio.run(main())
PY
```

## Plugin-only workaround

Inside `<plugin-root>/telegram-tvoice/__init__.py`, add a best-effort helper that mutates the in-memory Telegram priority tuple during plugin `register(ctx)` so `/tvoice` lands inside the top-30 menu. This avoids editing `~/.hermes/hermes-agent/**`.

Pattern:

```python
def _promote_tvoice_in_telegram_menu() -> None:
    try:
        from importlib import import_module

        commands = import_module("hermes_cli.commands")
        raw_priority = getattr(commands, "_TELEGRAM_MENU_PRIORITY", ()) or ()
        current: list[str] = [str(name) for name in raw_priority if str(name) != "tvoice"]
        for anchor in ("status", "commands", "help"):
            if anchor in current:
                current.insert(current.index(anchor) + 1, "tvoice")
                break
        else:
            current.insert(0, "tvoice")
        setattr(commands, "_TELEGRAM_MENU_PRIORITY", tuple(current))
    except Exception:
        pass


def register(ctx):
    _promote_tvoice_in_telegram_menu()
    ctx.register_command(
        "tvoice",
        handle_tvoice,
        "Switch Telegram/CLI Edge TTS voice: status, list [query], set <voice-id>, refresh",
        args_hint="status|list [query]|set <voice-id>|refresh|auto <text>",
    )
```

## Verification

After patching but before gateway restart, verify a fresh Hermes Python process places `tvoice` in the menu:

```bash
python -m py_compile "$(realpath ~/.hermes/plugins/telegram-tvoice)/__init__.py"
python - <<'PY'
from hermes_cli.plugins import get_plugin_commands
from hermes_cli.commands import telegram_menu_commands
assert 'tvoice' in get_plugin_commands()
menu, hidden = telegram_menu_commands(max_commands=30)
names = [n for n, _ in menu]
assert 'tvoice' in names and names.index('tvoice') < 30, names
print('ok', names.index('tvoice'), names)
PY
```

Gateway restart is still required for Telegram to receive a new `set_my_commands` payload. If the user explicitly says not to restart, patch and verify only; tell them `/tvoice status` can be typed manually and `/restart` or `hermes gateway restart` applies the menu update later.

## Post-restart but Telegram client still does not show `/tvoice`

If a restart happened and `get_my_commands()` for `Default`, `AllPrivateChats`, and/or `AllGroupChats` shows `tvoice`, but the Telegram client autocomplete still only shows older `/t...` entries like `/title` and `/topic`, suspect either Telegram client-side command-menu caching or a narrower chat-specific BotCommand scope.

Check the active chat ID from `$HERMES_HOME/channel_directory.json` or `$HERMES_HOME/sessions/sessions.json`, then inspect the chat-specific scope:

```bash
python - <<'PY'
import asyncio
from hermes_cli.config import get_env_value
from telegram import Bot, BotCommandScopeChat

CHAT_ID = 123456789  # replace with the active Telegram chat id

async def main():
    bot = Bot(get_env_value('TELEGRAM_BOT_TOKEN'))
    cmds = await bot.get_my_commands(scope=BotCommandScopeChat(chat_id=CHAT_ID))
    names = [c.command for c in cmds]
    print('chat_scope_count=', len(names), 'has_tvoice=', 'tvoice' in names, names)

asyncio.run(main())
PY
```

If broad scopes have `tvoice` but the user still cannot see it, force a chat-specific command payload for that DM/chat:

```bash
python - <<'PY'
import asyncio
from hermes_cli.config import get_env_value
from hermes_cli.commands import telegram_menu_commands
from telegram import Bot, BotCommand, BotCommandScopeChat

CHAT_ID = 123456789  # replace with the active Telegram chat id

async def main():
    bot = Bot(get_env_value('TELEGRAM_BOT_TOKEN'))
    menu, _hidden = telegram_menu_commands(max_commands=30)
    await bot.set_my_commands(
        [BotCommand(name, desc) for name, desc in menu],
        scope=BotCommandScopeChat(chat_id=CHAT_ID),
    )
    got = await bot.get_my_commands(scope=BotCommandScopeChat(chat_id=CHAT_ID))
    names = [c.command for c in got]
    assert 'tvoice' in names, names
    print('ok', names)

asyncio.run(main())
PY
```

After forcing chat scope, ask the user to close/reopen the Telegram chat or type the full `/tvoice status` once. Telegram clients can cache command suggestions even after Bot API reports the updated list.
