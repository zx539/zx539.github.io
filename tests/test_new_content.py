from datetime import date
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("new_content", Path(__file__).resolve().parents[1] / "scripts/new-content.py")
new_content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_content)


class NewContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="blog-content-test-")
        self.addCleanup(self.temp.cleanup)
        self.root_patch = patch.object(new_content, "ROOT", Path(self.temp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_weekly_uses_monday_across_year_boundary(self):
        path = new_content.create_draft("weekly", date(2026, 1, 1))
        self.assertEqual(path.name, "2025-12-29.md")
        text = path.read_text()
        self.assertIn("2025.12.29—2026.01.04", text)
        self.assertIn('date: "2025-12-29T00:00:00+08:00"', text)
        for heading in ("工作成果", "学习记录", "健身日记", "问题与复盘", "下周计划"):
            self.assertIn(f"## {heading}", text)

    def test_repeat_creation_preserves_existing_content(self):
        path = new_content.create_draft("weekly", date(2026, 10, 26))
        path.write_text("已经写下的工作记录", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            new_content.create_draft("weekly", date(2026, 11, 1))
        self.assertEqual(path.read_text(), "已经写下的工作记录")

    def test_photo_bundle_is_draft_and_does_not_overwrite_images(self):
        folder = new_content.ROOT / "content/photos/2026-10-30-walk"
        folder.mkdir(parents=True)
        (folder / "sunset.jpg").write_bytes(b"photo")
        path = new_content.create_draft("photo", date(2026, 10, 30), "walk", "傍晚散步")
        self.assertEqual(path, folder / "index.md")
        self.assertIn("draft: true", path.read_text())
        self.assertEqual((folder / "sunset.jpg").read_bytes(), b"photo")

    def test_rejects_path_traversal_in_content_names(self):
        for slug in ("../escape", "/tmp/escape", "a/b", "", "A B"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                new_content.create_draft("photo", date(2026, 10, 30), slug)


if __name__ == "__main__":
    unittest.main()
