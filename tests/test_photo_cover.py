import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HUGO = os.environ.get("HUGO_BIN") or shutil.which("hugo")
REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HUGO, "Hugo is required for cover rendering tests")
class PhotoCoverTests(unittest.TestCase):
    def build(self, cover, image):
        with tempfile.TemporaryDirectory(prefix="photo-cover-test-") as temp:
            root = Path(temp)
            (root / "hugo.toml").write_text('baseURL = "https://zxpage.online/"\ndisableKinds = ["taxonomy", "term", "RSS", "section"]\n')
            layouts = root / "layouts"
            (layouts / "partials/photos").mkdir(parents=True)
            shutil.copy2(REPO / "layouts/partials/photos/cover.html", layouts / "partials/photos/cover.html")
            (layouts / "index.html").write_text('{{ range site.RegularPages }}{{ partial "photos/cover.html" . }}{{ end }}')
            (layouts / "_default").mkdir()
            (layouts / "_default/single.html").write_text("{{ .Content }}")
            bundle = root / "content/photos/example"
            bundle.mkdir(parents=True)
            (bundle / "index.md").write_text(f'---\ntitle: Example\ndate: 2020-01-01\ncover: "{cover}"\n---\n')
            (bundle / image).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>')
            result = subprocess.run([HUGO, "--source", str(root), "--cacheDir", str(root / "cache"), "--noBuildLock"], text=True, capture_output=True)
            index = root / "public/index.html"
            return result, index.read_text() if index.exists() else ""

    def test_cover_filename_with_brackets_is_matched_literally(self):
        result, html = self.build("[1].svg", "[1].svg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("/photos/example/", html)

    def test_cover_pattern_does_not_silently_select_another_file(self):
        result, _ = self.build("[1].svg", "1.svg")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("找不到封面", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
