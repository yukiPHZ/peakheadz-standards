from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import generate_ai_context, quality_check


class GenerateAIContextTests(unittest.TestCase):
    def test_generation_is_deterministic_and_heading_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ORIGINAL.md").write_text(
                "# Product\n\n## 目的\n\n短い目的。\n\n## 長い記録\n\n含めない。\n",
                encoding="utf-8",
            )
            config = {
                "product": "Sample",
                "profile": "app",
                "standards_version": "1.0.0",
                "sections": [
                    {"output": "Purpose", "source": "ORIGINAL.md", "heading": "目的"}
                ],
            }
            first = generate_ai_context.generate(root, config)
            second = generate_ai_context.generate(root, config)
            self.assertEqual(first, second)
            self.assertIn("短い目的。", first)
            self.assertNotIn("含めない。", first)
            self.assertIn("AUTO-GENERATED FILE", first)
            self.assertNotIn("generated at", first.casefold())


class QualityCheckTests(unittest.TestCase):
    def write_config(self, root: Path) -> Path:
        config = {
            "profile": "app",
            "required_files": ["ORIGINAL.md", "README.md", "main.py"],
            "icon_paths": ["app.ico"],
            "scan_paths": ["main.py"],
            "user_text_paths": ["main.py"],
            "required_text": [
                {"path": "main.py", "text": "PEAKHEADZ", "label": "CompanyName"}
            ],
        }
        path = root / "peakheadz_quality.json"
        path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        return path

    def test_forbidden_credit_is_fail_and_generic_error_is_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ORIGINAL.md").write_text("# Original\n", encoding="utf-8")
            (root / "README.md").write_text("# Readme\n", encoding="utf-8")
            (root / "app.ico").write_bytes(b"ico")
            (root / "main.py").write_text(
                'CREDIT = "Vibe-Coded by Someone / PEAKHEADZ"\nUI = {"status_error": "エラー"}\n',
                encoding="utf-8",
            )
            config = self.write_config(root)
            findings = quality_check.run_checks(root, "app", config)
            self.assertTrue(any(item.code == "BRAND001" and item.severity == "FAIL" for item in findings))
            self.assertTrue(any(item.code == "UX002" and item.severity == "WARN" for item in findings))

    def test_clean_fixture_has_no_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ORIGINAL.md").write_text("# Original\n", encoding="utf-8")
            (root / "README.md").write_text("# Readme\n", encoding="utf-8")
            (root / "app.ico").write_bytes(b"ico")
            (root / "main.py").write_text(
                'COPYRIGHT = "© Yukihiko Kikuta / PEAKHEADZ"\nUI = {"status_error": "入力内容をご確認ください"}\n',
                encoding="utf-8",
            )
            config = self.write_config(root)
            findings = quality_check.run_checks(root, "app", config)
            self.assertFalse(any(item.severity == "FAIL" for item in findings))

    def test_web_globs_check_every_html_file_and_ignore_script_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public = root / "public"
            public.mkdir()
            (root / "README.md").write_text("# Readme\n", encoding="utf-8")
            (public / "index.html").write_text(
                '<html lang="ja"><head><title>Home</title></head><body>穏やかな案内<script>throw new Exception()</script></body></html>',
                encoding="utf-8",
            )
            (public / "about.html").write_text(
                '<html lang="ja"><head><title>About</title></head><body>概要</body></html>',
                encoding="utf-8",
            )
            config = {
                "profile": "web",
                "required_files": ["README.md", "public/index.html"],
                "scan_globs": ["public/**/*.html"],
                "user_text_globs": ["public/**/*.html"],
                "required_text_globs": [
                    {"glob": "public/**/*.html", "text": "<title>", "label": "title"}
                ],
            }
            path = root / "peakheadz_quality.json"
            path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            findings = quality_check.run_checks(root, "web", path)
            self.assertFalse(any(item.severity == "FAIL" for item in findings))
            self.assertFalse(any(item.code == "UX001" for item in findings))

            (public / "about.html").write_text('<html lang="ja"><body>概要</body></html>', encoding="utf-8")
            findings = quality_check.run_checks(root, "web", path)
            self.assertTrue(any(item.code == "WEB002" and item.severity == "FAIL" for item in findings))


if __name__ == "__main__":
    unittest.main()
