import importlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plugin_loader import PACKAGE_NAME, load_plugin_package


class AudioConversionTests(unittest.TestCase):
    def setUp(self):
        load_plugin_package()
        self.audio = importlib.import_module(f"{PACKAGE_NAME}.audio")

    def test_convert_mp3_runs_ffmpeg_with_options_before_output_path(self):
        with tempfile.TemporaryDirectory() as td:
            mp3_path = Path(td) / "sample.mp3"
            mp3_path.write_bytes(b"fake mp3")
            commands = []

            def fake_run(cmd, capture_output, timeout):
                commands.append(cmd)
                output_arg = next(arg for arg in cmd if str(arg).endswith(".ogg"))
                Path(output_arg).write_bytes(b"ogg")
                return subprocess.CompletedProcess(cmd, 0, b"", b"")

            with mock.patch.object(self.audio.shutil, "which", return_value="/usr/bin/ffmpeg"):
                with mock.patch.object(self.audio.subprocess, "run", side_effect=fake_run):
                    converted = self.audio._convert_audio_to_telegram_voice(str(mp3_path))

            cmd = commands[0]
            self.assertEqual(cmd[0], "/usr/bin/ffmpeg")
            self.assertIn("-nostdin", cmd)
            self.assertLess(cmd.index("-nostdin"), cmd.index("-i"))
            self.assertLess(cmd.index("-y"), len(cmd) - 1)
            self.assertLess(cmd.index("-loglevel"), len(cmd) - 1)
            self.assertEqual(cmd[-1], converted)
            self.assertTrue(converted.endswith(".ogg"))
            self.assertTrue(Path(converted).exists())

    def test_convert_mp3_to_telegram_voice_ogg_with_real_ffmpeg_when_available(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg/ffprobe unavailable")

        with tempfile.TemporaryDirectory() as td:
            mp3_path = Path(td) / "sample.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=channel_layout=mono:sample_rate=24000",
                    "-t",
                    "0.2",
                    "-q:a",
                    "9",
                    "-acodec",
                    "libmp3lame",
                    "-y",
                    "-loglevel",
                    "error",
                    str(mp3_path),
                ],
                check=True,
            )

            ogg_path = Path(self.audio._convert_audio_to_telegram_voice(str(mp3_path)))
            self.assertEqual(ogg_path.suffix, ".ogg")
            self.assertTrue(ogg_path.exists())

            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "default=nw=1:nk=1",
                    str(ogg_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(probe.stdout.strip(), "opus")


if __name__ == "__main__":
    unittest.main()
