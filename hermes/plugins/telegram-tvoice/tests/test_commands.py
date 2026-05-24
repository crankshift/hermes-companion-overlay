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


@contextlib.contextmanager
def fake_edge_tts_module(voices=None, error=None):
    module_name = "edge_tts"
    missing = object()
    original = sys.modules.get(module_name, missing)
    edge_tts = types.ModuleType(module_name)

    def list_voices():
        if error is not None:
            raise error
        return voices or []

    edge_tts.list_voices = list_voices
    sys.modules[module_name] = edge_tts

    try:
        yield
    finally:
        if original is missing:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = original


SAMPLE_EDGE_VOICES = [
    {
        "ShortName": "uk-UA-PolinaNeural",
        "Locale": "uk-UA",
        "Gender": "Female",
        "FriendlyName": "Microsoft Polina Online (Natural) - Ukrainian (Ukraine)",
        "VoiceTag": {"ContentCategories": ["General"]},
    },
    {
        "ShortName": "uk-UA-OstapNeural",
        "Locale": "uk-UA",
        "Gender": "Male",
        "FriendlyName": "Microsoft Ostap Online (Natural) - Ukrainian (Ukraine)",
        "VoiceTag": {"VoicePersonalities": ["Warm", "Positive"]},
    },
    {
        "ShortName": "pl-PL-ZofiaNeural",
        "Locale": "pl-PL",
        "Gender": "Female",
        "FriendlyName": "Microsoft Zofia Online (Natural) - Polish (Poland)",
    },
    {
        "ShortName": "pl-PL-MarekNeural",
        "Locale": "pl-PL",
        "Gender": "Male",
        "FriendlyName": "Microsoft Marek Online (Natural) - Polish (Poland)",
    },
    {
        "ShortName": "en-US-AndrewNeural",
        "Locale": "en-US",
        "Gender": "Male",
        "FriendlyName": "Microsoft Andrew Online (Natural) - English (United States)",
    },
    {
        "ShortName": "en-US-BrianMultilingualNeural",
        "Locale": "en-US",
        "Gender": "Male",
        "FriendlyName": "Microsoft BrianMultilingual Online (Natural) - English (United States)",
    },
    {
        "ShortName": "en-US-AvaNeural",
        "Locale": "en-US",
        "Gender": "Female",
        "FriendlyName": "Microsoft Ava Online (Natural) - English (United States)",
    },
    {
        "ShortName": "es-GT-AndresNeural",
        "Locale": "es-GT",
        "Gender": "Male",
        "FriendlyName": "Microsoft Andres Online (Natural) - Spanish (Guatemala)",
    },
    {
        "ShortName": "es-UY-MateoNeural",
        "Locale": "es-UY",
        "Gender": "Male",
        "FriendlyName": "Microsoft Mateo Online (Natural) - Spanish (Uruguay)",
    },
]


class CommandTests(unittest.TestCase):
    def setUp(self):
        load_plugin_package()
        self.commands = importlib.import_module(f"{PACKAGE_NAME}.commands")

    def test_handle_tvoice_list_returns_voice_catalog_not_status(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            result = self.commands.handle_tvoice("list")

        self.assertIn("Available Edge TTS voices:", result)
        self.assertIn("uk-UA-OstapNeural", result)
        self.assertIn("pl-PL-ZofiaNeural", result)
        self.assertNotIn("TVoice status:", result)

    def test_handle_tvoice_list_searches_runtime_catalog_by_locale_and_gender(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            uk_result = self.commands.handle_tvoice("list uk female")
            pl_result = self.commands.handle_tvoice("list pl female")
            en_result = self.commands.handle_tvoice("list en male")

        self.assertIn("uk-UA-PolinaNeural", uk_result)
        self.assertIn("Female", uk_result)
        self.assertNotIn("uk-UA-OstapNeural", uk_result)
        self.assertIn("pl-PL-ZofiaNeural", pl_result)
        self.assertIn("en-US-AndrewNeural", en_result)
        self.assertNotIn("en-US-AvaNeural", en_result)

    def test_handle_tvoice_list_country_code_matches_locale_region_only(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            result = self.commands.handle_tvoice("list ua")

        self.assertIn("uk-UA-OstapNeural", result)
        self.assertIn("uk-UA-PolinaNeural", result)
        self.assertNotIn("en-US-BrianMultilingualNeural", result)
        self.assertNotIn("es-GT-AndresNeural", result)
        self.assertNotIn("es-UY-MateoNeural", result)

    def test_handle_tvoice_list_country_code_shows_all_matches(self):
        voices = [
            {
                "ShortName": f"zz-UA-Test{i:02d}Neural",
                "Locale": "zz-UA",
                "Gender": "Female" if i % 2 else "Male",
                "FriendlyName": f"Test voice {i:02d}",
            }
            for i in range(25)
        ]

        with fake_edge_tts_module(voices):
            result = self.commands.handle_tvoice("list ua")

        self.assertIn("zz-UA-Test00Neural", result)
        self.assertIn("zz-UA-Test24Neural", result)
        self.assertNotIn("Showing first 20", result)

    def test_handle_tvoice_set_accepts_runtime_edge_voice_id(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("set en-US-AndrewNeural")

        self.assertIn("en-US-AndrewNeural", result)
        self.assertIn(("tts.provider", "edge"), writes)
        self.assertIn(("tts.edge.voice", "en-US-AndrewNeural"), writes)
        self.assertNotIn(("tts.default_voice_preset", "en-US-AndrewNeural"), writes)

    def test_handle_tvoice_set_rejects_unknown_voice_when_catalog_available(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("set en-US-NotAVoiceNeural")

        self.assertIn("Unknown Edge voice", result)
        self.assertIn("en-US-AndrewNeural", result)
        self.assertEqual([], writes)

    def test_handle_tvoice_set_rejects_removed_shortcut_aliases(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("set ua-ostap")

        self.assertIn("Unknown Edge voice", result)
        self.assertIn("uk-UA-OstapNeural", result)
        self.assertEqual([], writes)

    def test_handle_tvoice_rejects_removed_shortcut_command(self):
        with fake_config_module() as writes:
            result = self.commands.handle_tvoice("ua-ostap")

        self.assertIn("Unknown TVoice command", result)
        self.assertIn("/tvoice set <edge-voice-id>", result)
        self.assertEqual([], writes)

    def test_handle_tvoice_help_omits_shortcuts_and_presets(self):
        result = self.commands.handle_tvoice("help")

        self.assertIn("/tvoice set <edge-voice-id>", result)
        self.assertNotIn("ua-ostap", result)
        self.assertNotIn("pl-marek", result)
        self.assertNotIn("preset", result.lower())

    def test_handle_tvoice_without_args_returns_help(self):
        result = self.commands.handle_tvoice("")

        self.assertIn("TVoice commands:", result)
        self.assertIn("/tvoice status", result)
        self.assertIn("/tvoice list [country-code|query]", result)
        self.assertIn("/tvoice set <edge-voice-id>", result)
        self.assertNotIn("TVoice status:", result)

    def test_handle_tvoice_list_falls_back_when_edge_tts_fetch_fails(self):
        with fake_edge_tts_module(error=RuntimeError("offline")):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("list en male")

        self.assertIn("en-US-AndrewNeural", result)
        self.assertIn("fallback", result.lower())
        self.assertEqual([], writes)

    def test_handle_tvoice_refresh_refetches_runtime_catalog(self):
        voices = [next(voice for voice in SAMPLE_EDGE_VOICES if voice["ShortName"] == "en-US-AndrewNeural")]
        brian = {
            "ShortName": "en-US-BrianNeural",
            "Locale": "en-US",
            "Gender": "Male",
            "FriendlyName": "Microsoft Brian Online (Natural) - English (United States)",
        }

        with fake_edge_tts_module(voices):
            first = self.commands.handle_tvoice("list en male")
            voices[:] = [brian]
            cached = self.commands.handle_tvoice("list en male")
            refreshed = self.commands.handle_tvoice("refresh")
            after_refresh = self.commands.handle_tvoice("list en male")

        self.assertIn("en-US-AndrewNeural", first)
        self.assertIn("en-US-AndrewNeural", cached)
        self.assertIn("refreshed", refreshed.lower())
        self.assertIn("en-US-BrianNeural", after_refresh)
        self.assertNotIn("en-US-AndrewNeural", after_refresh)

    def test_handle_tvoice_auto_uses_polish_edge_voice_id(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("auto Cześć, mówimy po polsku")

        self.assertIn("pl-PL-MarekNeural", result)
        self.assertIn(("tts.provider", "edge"), writes)
        self.assertIn(("tts.edge.voice", "pl-PL-MarekNeural"), writes)
        self.assertNotIn(("tts.default_voice_preset", "pl-marek"), writes)

    def test_handle_tvoice_auto_uses_ukrainian_edge_voice_id(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("auto Привіт, говоримо українською")

        self.assertIn("uk-UA-OstapNeural", result)
        self.assertIn(("tts.provider", "edge"), writes)
        self.assertIn(("tts.edge.voice", "uk-UA-OstapNeural"), writes)
        self.assertNotIn(("tts.default_voice_preset", "ua-ostap"), writes)

    def test_handle_tvoice_auto_uses_english_male_voice(self):
        with fake_edge_tts_module(SAMPLE_EDGE_VOICES):
            with fake_config_module() as writes:
                result = self.commands.handle_tvoice("auto Hello, this is an English voice test")

        self.assertIn("en-US-AndrewNeural", result)
        self.assertIn(("tts.provider", "edge"), writes)
        self.assertIn(("tts.edge.voice", "en-US-AndrewNeural"), writes)
        self.assertNotIn(("tts.default_voice_preset", "en-US-AndrewNeural"), writes)

    def test_unknown_command_points_to_supported_command_surface(self):
        result = self.commands.handle_tvoice("does-not-exist")
        self.assertIn("Unknown TVoice command", result)
        self.assertIn("/tvoice list [country-code|query]", result)
        self.assertIn("/tvoice set <edge-voice-id>", result)
        self.assertNotIn("ua-ostap", result)

    def test_status_reports_config_and_runtime_dependencies(self):
        cfg = {
            "tts": {
                "provider": "edge",
                "edge": {"voice": "uk-UA-OstapNeural"},
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
