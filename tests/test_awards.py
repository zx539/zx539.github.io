import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HUGO = os.environ.get("HUGO_BIN") or shutil.which("hugo")
REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HUGO, "Hugo is required for awards rendering tests")
class AwardsTests(unittest.TestCase):
    def build(self, image_exists=True):
        temp = tempfile.TemporaryDirectory(prefix="awards-test-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        # Use the real static mount rules, including exclusions for unfinished documents.
        (root / "hugo.toml").write_text((REPO / "hugo.toml").read_text())
        layouts = root / "layouts"
        (layouts / "partials").mkdir(parents=True)
        shutil.copy2(REPO / "layouts/partials/awards.html", layouts / "partials/awards.html")
        (layouts / "index.html").write_text('{{ partial "awards.html" . }}')
        (root / "assets/js").mkdir(parents=True)
        shutil.copy2(REPO / "assets/js/awards.js", root / "assets/js/awards.js")
        (root / "data").mkdir()
        (root / "data/profile.json").write_text(json.dumps({"awards": [
            {"year": 2025, "title": "National competition", "level": "Gold", "scope": "national", "image": "images/award/national.svg", "file": "images/award/national.pdf"},
            {"year": 2025, "title": "Provincial competition", "level": "First", "scope": "provincial"},
        ]}))
        for folder in ("award", "patent", "software-copyright"):
            (root / "static/images" / folder).mkdir(parents=True)
        if image_exists:
            (root / "static/images/award/national.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        (root / "static/images/award/national.pdf").write_bytes(b"%PDF-1.7")
        for folder in ("patent", "software-copyright"):
            (root / "static/images" / folder / "not-public.pdf").write_bytes(b"private draft")
        result = subprocess.run([HUGO, "--source", str(root), "--destination", str(root / "public"), "--cacheDir", str(root / "cache"), "--noBuildLock"], text=True, capture_output=True)
        return result, root / "public"

    def test_groups_and_certificate_links_preserve_unfinished_award(self):
        result, output = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        html = (output / "index.html").read_text()
        national = html.split('id="awards-national-heading"', 1)[1].split('</section>', 1)[0]
        provincial = html.split('id="awards-provincial-heading"', 1)[1].split('</section>', 1)[0]
        self.assertIn('data-award-preview', national)
        self.assertIn('National competition', national)
        self.assertNotIn('Provincial competition', national)
        self.assertIn('Provincial competition', provincial)
        self.assertIn('证书待补充', provincial)
        self.assertNotIn('data-award-preview', provincial)

    def test_unfinished_documents_are_not_published(self):
        result, output = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((output / "images/award/national.pdf").is_file())
        for folder in ("patent", "software-copyright"):
            self.assertEqual(list((output / "images" / folder).rglob("*.*")), [])

    def test_missing_certificate_preview_stops_build(self):
        result, _ = self.build(image_exists=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('找不到奖项文件', result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
