import importlib
import unittest

from plugin_loader import PACKAGE_NAME, load_plugin_package


class SanitizerTests(unittest.TestCase):
    def setUp(self):
        load_plugin_package()
        self.sanitizer = importlib.import_module(f"{PACKAGE_NAME}.sanitizer")

    def test_strip_footer_for_tts_removes_runtime_footer(self):
        text = "Ось нормальна відповідь.\n\ngpt-5.5 · 17% · ~/workspace"
        self.assertEqual(self.sanitizer._strip_footer_for_tts(text), "Ось нормальна відповідь.")

    def test_strip_footer_for_tts_keeps_normal_middle_dot_text(self):
        text = "alpha · beta · release notes are allowed, це не footer."
        self.assertEqual(self.sanitizer._strip_footer_for_tts(text), text)

    def test_sanitize_text_for_tts_removes_footer_and_emoji(self):
        text = "Окей ✅ зроблено 😄\n\n🤖 gpt-5.5 · 17% · ~/workspace"
        self.assertEqual(self.sanitizer._sanitize_text_for_tts(text), "Окей зроблено")

    def test_sanitize_text_for_tts_removes_ascii_smileys(self):
        self.assertEqual(self.sanitizer._sanitize_text_for_tts("Готово :)"), "Готово")


if __name__ == "__main__":
    unittest.main()
