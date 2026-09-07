"""Catch unusable PDF rendering before spending on document readers."""

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check


class PopplerPreflightTest(unittest.TestCase):
    def test_missing_program_gives_platform_install_instructions(self):
        for platform, command in (
            ("win32", "winget install --id oschwartz10612.Poppler --exact --source winget"),
            ("darwin", "brew install poppler"),
            ("linux", "sudo apt install poppler-utils"),
        ):
            with self.subTest(platform=platform), patch.object(check.sys, "platform", platform), \
                    patch.object(check.shutil, "which", return_value=None):
                error = check.check_poppler()
                self.assertIn(command, error)
                self.assertIn("restart the terminal and Claude Code", error)

    def test_program_on_path_that_cannot_start_fails_cleanly(self):
        with patch.object(check.shutil, "which", return_value="pdftoppm"), \
                patch.object(check.subprocess, "run", side_effect=OSError("missing DLL")):
            self.assertIn("missing DLL", check.check_poppler())

    def test_nonzero_render_exit_fails_with_bounded_diagnostics(self):
        result = subprocess.CompletedProcess([], 99, stdout="", stderr="Unsupported -jpeg\n" * 100)
        with patch.object(check.shutil, "which", return_value="pdftoppm"), \
                patch.object(check.subprocess, "run", return_value=result):
            error = check.check_poppler()
        self.assertIn("exit 99", error)
        self.assertIn("Unsupported -jpeg", error)
        self.assertNotIn("\n", error)
        self.assertLess(len(error), 600)

    def test_zero_exit_without_jpeg_is_not_a_pass(self):
        # Some unsuitable builds can print help without producing the requested format.
        for image in (None, b"P6\n1 1\n255\n\xff\xff\xff", b"\xff\xd8\xfftruncated"):
            def render(command, **kwargs):
                if image is not None:
                    Path(command[-1]).with_suffix(".jpg").write_bytes(image)
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with self.subTest(image=image), patch.object(check.shutil, "which", return_value="pdftoppm"), \
                    patch.object(check.subprocess, "run", side_effect=render):
                self.assertIn("produced no JPEG", check.check_poppler())

    def test_hung_renderer_is_reported_without_traceback(self):
        with patch.object(check.shutil, "which", return_value="pdftoppm"), \
                patch.object(check.subprocess, "run", side_effect=subprocess.TimeoutExpired("pdftoppm", 15)):
            self.assertIn("timed out", check.check_poppler())

    def test_temporary_probe_is_cleaned_up_after_failure(self):
        probes = []

        def render(command, **kwargs):
            probes.append(Path(command[-2]))
            self.assertTrue(probes[-1].read_bytes().startswith(b"%PDF-"))
            self.assertIn("-jpeg", command)
            raise OSError("cannot start")

        with patch.object(check.shutil, "which", return_value="pdftoppm"), \
                patch.object(check.subprocess, "run", side_effect=render):
            self.assertIsNotNone(check.check_poppler())
        self.assertEqual(len(probes), 1)
        self.assertFalse(probes[0].parent.exists())

    def test_preflight_exit_code_blocks_missing_renderer(self):
        # Exercise the CLI wiring without touching the active kit's work/ or out/.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for error, expected in (("pdftoppm not on PATH", 1), (None, 0)):
                output = io.StringIO()
                with self.subTest(error=error), \
                        patch.object(check.sys, "argv", ["check.py"]), \
                        patch.object(check, "WORK", root / "work"), \
                        patch.object(check, "OUT", root / "out"), \
                        patch.object(check, "check_poppler", return_value=error), \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(check.main(), expected)
                if error:
                    self.assertIn("FAIL Poppler:", output.getvalue())
                    self.assertNotIn("All checks passed", output.getvalue())
                else:
                    self.assertIn("ok  Poppler", output.getvalue())

    @unittest.skipUnless(shutil.which("pdftoppm"), "Poppler not installed on test host")
    def test_installed_poppler_actually_renders_probe(self):
        self.assertIsNone(check.check_poppler())


if __name__ == "__main__":
    unittest.main()
