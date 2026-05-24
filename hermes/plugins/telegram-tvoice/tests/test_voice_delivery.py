import importlib.util
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

PLUGIN_PATH = Path(__file__).resolve().parents[1] / "__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("telegram_tvoice_plugin", PLUGIN_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VoiceDeliveryTests(unittest.TestCase):
    def test_strip_footer_for_tts_removes_runtime_footer(self):
        plugin = load_plugin()
        text = "Ось нормальна відповідь.\n\ngpt-5.5 · 17% · ~/workspace"
        self.assertEqual(plugin._strip_footer_for_tts(text), "Ось нормальна відповідь.")

    def test_strip_footer_for_tts_keeps_normal_middle_dot_text(self):
        plugin = load_plugin()
        text = "alpha · beta · release notes are allowed, це не footer."
        self.assertEqual(plugin._strip_footer_for_tts(text), text)

    def test_sanitize_text_for_tts_removes_footer_and_emoji(self):
        plugin = load_plugin()
        text = "Окей ✅ зроблено 😄\n\n🤖 gpt-5.5 · 17% · ~/workspace"
        self.assertEqual(plugin._sanitize_text_for_tts(text), "Окей зроблено")

    def test_sanitize_text_for_tts_removes_ascii_smileys(self):
        plugin = load_plugin()
        self.assertEqual(plugin._sanitize_text_for_tts("Готово :)"), "Готово")

    def test_install_tts_text_filter_wraps_gateway_prepare_and_tool_entrypoint(self):
        plugin = load_plugin()

        module_names = [
            "tools",
            "tools.tts_tool",
            "gateway",
            "gateway.platforms",
            "gateway.platforms.base",
        ]
        missing = object()
        originals = {name: (sys.modules[name] if name in sys.modules else missing) for name in module_names}

        tools_mod = types.ModuleType("tools")
        tts_mod = types.ModuleType("tools.tts_tool")

        def fake_strip(text):
            return f"strip:{text}"

        def fake_tts(text, output_path=None):
            return {"text": text, "output_path": output_path}

        setattr(tts_mod, "_strip_markdown_for_tts", fake_strip)
        setattr(tts_mod, "text_to_speech_tool", fake_tts)
        setattr(tools_mod, "tts_tool", tts_mod)

        gateway_mod = types.ModuleType("gateway")
        platforms_mod = types.ModuleType("gateway.platforms")
        base_mod = types.ModuleType("gateway.platforms.base")

        class BasePlatformAdapter:
            def prepare_tts_text(self, text):
                return text

        setattr(base_mod, "BasePlatformAdapter", BasePlatformAdapter)
        setattr(platforms_mod, "base", base_mod)
        setattr(gateway_mod, "platforms", platforms_mod)

        try:
            sys.modules.update({
                "tools": tools_mod,
                "tools.tts_tool": tts_mod,
                "gateway": gateway_mod,
                "gateway.platforms": platforms_mod,
                "gateway.platforms.base": base_mod,
            })

            plugin._install_tts_text_filter()
            noisy = "Привіт 😄\n\ngpt-5.5 · 17% · ~/workspace"

            self.assertEqual(BasePlatformAdapter().prepare_tts_text(noisy), "Привіт")
            self.assertEqual(getattr(tts_mod, "text_to_speech_tool")(text=noisy, output_path="x.ogg"), {
                "text": "Привіт",
                "output_path": "x.ogg",
            })
            self.assertEqual(getattr(tts_mod, "_strip_markdown_for_tts")(noisy), "strip:Привіт")
        finally:
            for name, module in originals.items():
                if module is missing:
                    sys.modules.pop(name, None)
                else:
                    assert isinstance(module, types.ModuleType)
                    sys.modules[name] = module

    def test_convert_mp3_to_telegram_voice_ogg(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg/ffprobe unavailable")
        plugin = load_plugin()
        with tempfile.TemporaryDirectory() as td:
            mp3_path = Path(td) / "sample.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "lavfi",
                    "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
                    "-t", "0.2",
                    "-q:a", "9",
                    "-acodec", "libmp3lame",
                    str(mp3_path),
                    "-y",
                    "-loglevel", "error",
                ],
                check=True,
            )

            ogg_path = Path(plugin._convert_audio_to_telegram_voice(str(mp3_path)))
            self.assertEqual(ogg_path.suffix, ".ogg")
            self.assertTrue(ogg_path.exists())

            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "default=nw=1:nk=1",
                    str(ogg_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(probe.stdout.strip(), "opus")


if __name__ == "__main__":
    unittest.main()
