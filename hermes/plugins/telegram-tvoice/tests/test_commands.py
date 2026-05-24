import contextlib
import importlib
import sys
import types
import unittest
from unittest import mock

from plugin_loader import PACKAGE_NAME, load_plugin_package


@contextlib.contextmanager
def fake_config_module(load_config=None, env=None):
    module_names = ["hermes_cli", "hermes_cli.config"]
    missing = object()
    originals = {name: sys.modules.get(name, missing) for name in module_names}
    writes = []

    hermes_cli = types.ModuleType("hermes_cli")
    config = types.ModuleType("hermes_cli.config")

    def set_config_value(key, value):
        writes.append((key, value))

    config.set_config_value = set_config_value
    config.load_config = lambda: load_config if load_config is not None else {}
    config.get_config_path = lambda: "/tmp/hermes/config.yaml"
    config.get_env_value = lambda key: (env or {}).get(key)
    hermes_cli.config = config

    sys.modules["hermes_cli"] = hermes_cli
    sys.modules["hermes_cli.config"] = config

    try:
        yield writes
    finally:
        for name, module in originals.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class CommandTests(unittest.TestCase):
    def setUp(self):
        load_plugin_package()
        self.commands = importlib.import_module(f"{PACKAGE_NAME}.commands")

    def test_apply_preset_writes_edge_voice_config(self):
        with fake_config_module() as writes:
            result = self.commands._apply_preset("ua")

        self.assertIn("ua-ostap", result)
        self.assertIn(("tts.provider", "edge"), writes)
        self.assertIn(("tts.edge.voice", "uk-UA-OstapNeural"), writes)
        self.assertIn(("tts.default_voice_preset", "ua-ostap"), writes)
        self.assertIn(("tts.language_voice_map.pl", "pl-marek"), writes)

    def test_handle_tvoice_list_returns_preset_list_not_status(self):
        result = self.commands.handle_tvoice("list")

        self.assertIn("Available TVoice presets:", result)
        self.assertIn("ua-ostap", result)
        self.assertIn("pl-marek", result)
        self.assertNotIn("TVoice status:", result)

    def test_handle_tvoice_presets_returns_preset_list(self):
        result = self.commands.handle_tvoice("presets")
        self.assertIn("Available TVoice presets:", result)

    def test_handle_tvoice_auto_uses_polish_preset(self):
        with fake_config_module() as writes:
            result = self.commands.handle_tvoice("auto Cześć, mówimy po polsku")

        self.assertIn("pl-marek", result)
        self.assertIn(("tts.edge.voice", "pl-PL-MarekNeural"), writes)

    def test_unknown_preset_lists_known_presets(self):
        result = self.commands.handle_tvoice("does-not-exist")
        self.assertIn("Unknown preset", result)
        self.assertIn("ua-ostap", result)
        self.assertIn("pl-marek", result)

    def test_status_reports_config_and_runtime_dependencies(self):
        cfg = {
            "tts": {
                "provider": "edge",
                "edge": {"voice": "uk-UA-OstapNeural"},
                "default_voice_preset": "ua-ostap",
                "language_voice_map": {"uk": "ua-ostap", "pl": "pl-marek"},
            },
            "stt": {"provider": "groq", "groq": {"model": "whisper-large-v3-turbo"}},
        }
        with fake_config_module(load_config=cfg, env={"GROQ_API_KEY": "secret"}):
            with mock.patch.object(self.commands.shutil, "which", return_value="/usr/bin/ffmpeg"):
                result = self.commands._status()

        self.assertIn("- Config: /tmp/hermes/config.yaml", result)
        self.assertIn("- TTS provider: edge", result)
        self.assertIn("- Active voice: uk-UA-OstapNeural", result)
        self.assertIn("- Groq key: present", result)
        self.assertIn("- ffmpeg: /usr/bin/ffmpeg", result)


if __name__ == "__main__":
    unittest.main()
