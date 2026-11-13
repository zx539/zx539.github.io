import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
HUGO = os.environ.get("HUGO_BIN") or shutil.which("hugo")


@unittest.skipUnless(HUGO and shutil.which("rsync") and shutil.which("flock"), "Hugo, rsync and flock required")
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="myblog-deploy-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source"
        self.checkout = self.root / "checkout"
        self.website = self.root / "website"
        self.git("init", "-b", "published", str(self.source), cwd=self.root)
        self.git("config", "user.name", "Deploy Test")
        self.git("config", "user.email", "deploy@example.invalid")
        (self.source / "layouts").mkdir()
        (self.source / "layouts/index.html").write_text('{{ readFile "message.txt" }}')
        (self.source / "hugo.toml").write_text(
            'baseURL = "https://example.invalid/"\ndisableKinds = ["taxonomy", "term", "RSS"]\n'
        )
        (self.source / ".gitignore").write_text(".hugo_build.lock\nresources/\n")
        self.commit("old site")
        self.git("clone", str(self.source), str(self.checkout), cwd=self.root)
        self.env = {
            **os.environ,
            "REPO_DIR": str(self.checkout),
            "DEPLOY_DIR": str(self.website),
            "DEPLOY_BRANCH": "published",
            "DEPLOY_REMOTE": "origin",
            "HUGO_BIN": HUGO,
        }

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=cwd or self.source, text=True, capture_output=True, check=True,
        )

    def commit(self, message):
        (self.source / "message.txt").write_text(message)
        self.git("add", ".")
        self.git("commit", "-m", message)

    def deploy(self):
        return subprocess.run(
            ["bash", str(ROOT / "scripts/deploy.sh")],
            env=self.env, text=True, capture_output=True, timeout=30,
        )

    def test_fetch_build_publish_and_keep_old_site_when_build_fails(self):
        self.website.mkdir()
        (self.website / "obsolete.html").write_text("obsolete")
        self.commit("new site")
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.website / "index.html").read_text().strip(), "new site")
        self.assertFalse((self.website / "obsolete.html").exists())

        (self.source / "layouts/index.html").write_text("{{ invalid_template_function }}")
        self.commit("broken build")
        result = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("building Hugo site", result.stdout)
        self.assertIn("invalid_template_function", result.stdout + result.stderr)
        self.assertEqual((self.website / "index.html").read_text().strip(), "new site")

    def test_local_changes_are_preserved_and_block_deployment(self):
        local = self.checkout / "message.txt"
        local.write_text("server changes")
        self.commit("remote changes")
        result = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local changes", result.stderr)
        self.assertEqual(local.read_text(), "server changes")
        self.assertFalse(self.website.exists())


class WebhookTests(unittest.TestCase):
    def test_authentication_filtering_and_push_during_deployment(self):
        with tempfile.TemporaryDirectory(prefix="myblog-webhook-test-") as temp:
            root = Path(temp)
            script = root / "deploy.sh"
            # The first deployment waits while we deliver the next push.
            script.write_text(
                'set -eu\ncd "$(dirname "$0")"\necho started >> runs\n'
                'for ((i=0; i<500; i++)); do\n'
                '  [[ -f release ]] && exit 0\n  sleep 0.02\ndone\nexit 1\n'
            )
            secret = "test-secret-for-gitcode"
            env = {
                **os.environ,
                "WEBHOOK_HOST": "127.0.0.1",
                "WEBHOOK_PORT": "0",
                "WEBHOOK_SECRET": secret,
                "DEPLOY_SCRIPT": str(script),
                "DEPLOY_LOG": str(root / "deploy.log"),
                "DEPLOY_BRANCH": "published",
            }
            with (root / "service.log").open("w+") as service_log:
                process = subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts/gitcode-webhook.py")],
                    env=env, stdout=subprocess.PIPE, stderr=service_log, text=True,
                )
                try:
                    address = process.stdout.readline().strip()
                    service_log.flush()
                    if not address:
                        service_log.seek(0)
                        self.fail(service_log.read())
                    self.assertTrue(address.startswith("listening on http://127.0.0.1:"), address)
                    port = int(address.split(":")[-1].split("/")[0])

                    def post(payload, headers):
                        body = json.dumps(payload).encode()
                        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                        try:
                            connection.request("POST", "/gitcode-webhook", body, headers)
                            response = connection.getresponse()
                            return response.status, json.loads(response.read())
                        finally:
                            connection.close()

                    payload = {"object_kind": "push", "ref": "refs/heads/published"}
                    self.assertEqual(post(payload, {})[0], 401)
                    token = {"X-GitCode-Token": secret}
                    self.assertEqual(post([], token)[0], 400)
                    self.assertEqual(post({**payload, "ref": "refs/heads/other"}, token)[1]["ignored"], "branch")
                    self.assertEqual(post({**payload, "object_kind": "tag_push"}, token)[1]["ignored"], "event")
                    self.assertEqual(post({**payload, "after": "0" * 40}, token)[1]["ignored"], "deleted branch")
                    self.assertFalse((root / "runs").exists())

                    signature = "sha256=" + hmac.new(secret.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
                    self.assertEqual(post(payload, {"X-GitCode-Signature-256": signature})[0], 202)
                    self.wait_for_runs(root / "runs", 1)
                    self.assertEqual(post(payload, token)[0], 202)
                    (root / "release").touch()
                    self.wait_for_runs(root / "runs", 2)
                finally:
                    # Let any deployment child exit before terminating the service.
                    (root / "release").touch()
                    process.terminate()
                    process.wait(timeout=5)
                    process.stdout.close()

    def wait_for_runs(self, path, expected):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if path.exists() and len(path.read_text().splitlines()) >= expected:
                return
            time.sleep(0.02)
        self.fail(f"expected {expected} deployments")


if __name__ == "__main__":
    unittest.main()
