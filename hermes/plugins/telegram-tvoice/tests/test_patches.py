import asyncio
import contextlib
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from plugin_loader import PACKAGE_NAME, load_plugin_package


@contextlib.contextmanager
def fake_telegram_adapter(adapter_cls):
    module_names = ["gateway", "gateway.platforms", "gateway.platforms.telegram"]
    missing = object()
    originals = {name: sys.modules.get(name, missing) for name in module_names}

    gateway = types.ModuleType("gateway")
    platforms = types.ModuleType("gateway.platforms")
    telegram = types.ModuleType("gateway.platforms.telegram")
    telegram.TelegramAdapter = adapter_cls
    platforms.telegram = telegram
    gateway.platforms = platforms
    sys.modules.update({
        "gateway": gateway,
        "gateway.platforms": platforms,
        "gateway.platforms.telegram": telegram,
    })

    try:
        yield
    finally:
        for name, module in originals.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class PatchTests(unittest.TestCase):
    def setUp(self):
        load_plugin_package()
        self.patches = importlib.import_module(f"{PACKAGE_NAME}.patches")

    def test_telegram_voice_patch_ignores_missing_send_voice(self):
        class TelegramAdapter:
            pass

        with fake_telegram_adapter(TelegramAdapter):
            self.patches._install_telegram_voice_delivery_patch()

        self.assertFalse(hasattr(TelegramAdapter, "_telegram_tvoice_ogg_patch_installed"))

    def test_telegram_voice_patch_ignores_non_callable_send_voice(self):
        class TelegramAdapter:
            send_voice = None

        with fake_telegram_adapter(TelegramAdapter):
            self.patches._install_telegram_voice_delivery_patch()

        self.assertIsNone(TelegramAdapter.send_voice)
        self.assertFalse(hasattr(TelegramAdapter, "_telegram_tvoice_ogg_patch_installed"))

    def test_telegram_voice_patch_converts_before_send_and_cleans_up_once(self):
        calls = []

        class TelegramAdapter:
            async def send_voice(self, chat_id, audio_path, caption=None, reply_to=None, metadata=None, **kwargs):
                calls.append({
                    "chat_id": chat_id,
                    "audio_path": audio_path,
                    "caption": caption,
                    "reply_to": reply_to,
                    "metadata": metadata,
                    "kwargs": kwargs,
                    "exists_during_send": Path(audio_path).exists(),
                })
                return "sent"

        with tempfile.TemporaryDirectory() as td:
            original = Path(td) / "voice.mp3"
            converted = Path(td) / "voice.ogg"
            original.write_bytes(b"mp3")

            def convert(path):
                converted.write_bytes(b"ogg")
                return str(converted)

            with fake_telegram_adapter(TelegramAdapter):
                with mock.patch.object(self.patches, "_convert_audio_to_telegram_voice", side_effect=convert) as convert_mock:
                    self.patches._install_telegram_voice_delivery_patch()
                    first_wrapper = TelegramAdapter.send_voice
                    self.patches._install_telegram_voice_delivery_patch()
                    self.assertIs(TelegramAdapter.send_voice, first_wrapper)

                    result = asyncio.run(
                        TelegramAdapter().send_voice(
                            "chat",
                            str(original),
                            caption="caption",
                            reply_to="reply",
                            metadata={"m": "v"},
                            parse_mode="HTML",
                        )
                    )

                    self.assertEqual(result, "sent")
                    self.assertEqual(convert_mock.call_count, 1)
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(calls[0]["audio_path"], str(converted))
                    self.assertTrue(calls[0]["exists_during_send"])
                    self.assertFalse(converted.exists())
                    self.assertEqual(calls[0]["kwargs"], {"parse_mode": "HTML"})

    def test_tts_text_filter_is_idempotent(self):
        module_names = [
            "tools",
            "tools.tts_tool",
            "gateway",
            "gateway.platforms",
            "gateway.platforms.base",
        ]
        missing = object()
        originals = {name: sys.modules.get(name, missing) for name in module_names}

        tools_mod = types.ModuleType("tools")
        tts_mod = types.ModuleType("tools.tts_tool")

        def fake_strip(text):
            return f"strip:{text}"

        def fake_tts(text, output_path=None):
            return {"text": text, "output_path": output_path}

        tts_mod._strip_markdown_for_tts = fake_strip
        tts_mod.text_to_speech_tool = fake_tts
        tools_mod.tts_tool = tts_mod

        gateway_mod = types.ModuleType("gateway")
        platforms_mod = types.ModuleType("gateway.platforms")
        base_mod = types.ModuleType("gateway.platforms.base")

        class BasePlatformAdapter:
            def prepare_tts_text(self, text):
                return text

        base_mod.BasePlatformAdapter = BasePlatformAdapter
        platforms_mod.base = base_mod
        gateway_mod.platforms = platforms_mod

        try:
            sys.modules.update({
                "tools": tools_mod,
                "tools.tts_tool": tts_mod,
                "gateway": gateway_mod,
                "gateway.platforms": platforms_mod,
                "gateway.platforms.base": base_mod,
            })

            self.patches._install_tts_text_filter()
            first_prepare = BasePlatformAdapter.prepare_tts_text
            first_tts = tts_mod.text_to_speech_tool
            self.patches._install_tts_text_filter()

            noisy = "Привіт 😄\n\ngpt-5.5 · 17% · ~/workspace"
            self.assertIs(BasePlatformAdapter.prepare_tts_text, first_prepare)
            self.assertIs(tts_mod.text_to_speech_tool, first_tts)
            self.assertEqual(BasePlatformAdapter().prepare_tts_text(noisy), "Привіт")
            self.assertEqual(tts_mod.text_to_speech_tool(noisy, output_path="x.ogg"), {
                "text": "Привіт",
                "output_path": "x.ogg",
            })
            self.assertEqual(tts_mod._strip_markdown_for_tts(noisy), "strip:Привіт")
        finally:
            for name, module in originals.items():
                if module is missing:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
