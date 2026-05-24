# telegram-tvoice TTS sanitizer pattern

Session-derived detail for plugin-only Telegram voice fixes.

## Problem

Telegram voice delivery can be correct (`.ogg`/Opus voice bubble) while the spoken audio still reads things that should remain visual-only:

- Hermes runtime footer lines, e.g. `gpt-5.5 · 17% · ~/workspace`
- emoji and smileys, e.g. `✅`, `😄`, `🤖`, `:)`

A too-narrow fix is to patch only `tools.tts_tool._strip_markdown_for_tts`. That misses Telegram auto-TTS because gateway voice replies prepare text earlier.

## Correct runtime path to cover

Telegram auto-TTS for voice replies goes through:

1. `BasePlatformAdapter.prepare_tts_text(text_content)`
2. `tools.tts_tool.text_to_speech_tool(text=speech_text)`
3. platform delivery via `play_tts()` / `send_voice()`

Direct/manual TTS tool calls can enter at `text_to_speech_tool` without the gateway `prepare_tts_text` step. Streaming/direct TTS helpers can still use `_strip_markdown_for_tts`.

## Plugin-only fix shape

In a user plugin, install deterministic wrappers during `register(ctx)`:

- wrap `gateway.platforms.base.BasePlatformAdapter.prepare_tts_text`
- wrap `tools.tts_tool.text_to_speech_tool`
- optionally wrap `tools.tts_tool._strip_markdown_for_tts` for streaming/direct compatibility

The sanitizer should:

1. remove emoji / dingbats / ZWJ variation selectors / ASCII smileys;
2. then remove the final Hermes runtime footer line matching `model · percent · cwd` shape;
3. collapse excess whitespace;
4. return only the spoken text;
5. leave visible Telegram text/caption untouched.

Do not use `transform_llm_output` alone for this: the runtime footer may be appended after normal LLM-output hooks, and changing final visible text would remove a footer the user may still want to see.

## Minimal detection rules

Footer heuristic:

- line contains ` · ` separators;
- line is short (avoid eating prose);
- at least one segment is a context percent such as `17%` or `100%`, or one segment looks like cwd (`~`, `~/...`, `/...`, `.`, `..`).

Emoji heuristic:

- strip Unicode ranges for flags, pictographs, emoticons, dingbats/misc symbols, skin tones, variation selectors, ZWJ, and keycap;
- strip common ASCII smileys with a bounded regex.

## Verification targets

Add tests for:

- footer removed from final spoken text;
- normal middle-dot prose such as `alpha · beta · release notes` preserved;
- emoji/smileys removed;
- plugin register installs wrappers on `BasePlatformAdapter.prepare_tts_text` and `tools.tts_tool.text_to_speech_tool`;
- direct MP3/M4A/WAV/FLAC paths passed to Telegram `send_voice()` are converted to `.ogg`/Opus before upload.

Smoke sample:

```text
Input:  Окей ✅😄

        gpt-5.5 · 17% · ~/workspace
Speech: Окей
```

## Skill vs plugin boundary

A skill can document how spoken replies should be prepared, but it does not execute inside the already-running gateway audio path. Runtime stripping belongs in plugin/core code. The skill should reference the policy and verification pattern; the plugin should implement it deterministically.
