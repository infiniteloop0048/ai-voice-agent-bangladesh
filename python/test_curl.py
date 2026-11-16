import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(shutil.which("bash"), "bash is not installed")
class CurlTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.temp = tempfile.TemporaryDirectory(prefix=".offline-check-", dir=self.root)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        fake = self.directory / "curl"
        fake.write_text("#!" + sys.executable + "\n" + '''
import os
from pathlib import Path
import sys
args = sys.argv[1:]
assert args[args.index('--max-time') + 1] in ('10', '120')
assert args[args.index('--connect-timeout') + 1] == '10'
Path(args[args.index('--output') + 1]).write_bytes(os.environ['CHECK_BODY'].encode())
Path(args[args.index('--dump-header') + 1]).write_text('Content-Type: ' + os.environ['CHECK_TYPE'] + '\\r\\n')
sys.stdout.write(os.environ['CHECK_STATUS'])
''')
        fake.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.directory) + os.pathsep + os.environ["PATH"],
                        VOICE_API_URL="https://example.com/api/v1",
                        VOICE_API_KEY="vk_live_xxxxxxxxxxxxxxxxxxxx",
                        VOICE_WEBHOOK_SECRET="change-me",
                        CHECK_STATUS="202", CHECK_BODY="{}", CHECK_TYPE="application/json",
                        TMPDIR=str(self.directory))

    def run_script(self, name, *arguments):
        return subprocess.run(["bash", str(self.root / "curl" / name), *map(str, arguments)],
                              env=self.env, capture_output=True, text=True, check=False, timeout=10)

    def test_send(self):
        result = self.run_script("send-call.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "{}")
        self.assertIn("HTTP 202", result.stderr)

    def test_error_status_body_and_key_redaction(self):
        self.env.update(CHECK_STATUS="401", CHECK_BODY="bad " + self.env["VOICE_API_KEY"])
        result = self.run_script("balance.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HTTP 401: bad [redacted]", result.stderr)
        self.assertNotIn(self.env["VOICE_API_KEY"], result.stderr)

    def test_queued_voiceover_does_not_create_audio_file(self):
        output = self.directory / "voiceover.mp3"
        payload = self.directory / "request.json"
        payload.write_text('{"voice_id":"VOICE_ID","text":"আপনার অর্ডারটি আজ পাঠানো হয়েছে।","format":"mp3"}')
        result = self.run_script("voiceover.sh", "create", payload, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "{}")
        self.assertFalse(output.exists())

    def test_audio_voiceover_saves_bytes(self):
        self.env.update(CHECK_STATUS="200", CHECK_TYPE="audio/mpeg", CHECK_BODY="audio")
        output = self.directory / "voiceover.mp3"
        result = self.run_script("voiceover.sh", "audio", "VOICEOVER_ID", "mp3", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), b"audio")
        self.assertEqual(result.stdout, "")

    def test_missing_environment(self):
        for name in ("VOICE_API_URL", "VOICE_API_KEY", "VOICE_WEBHOOK_SECRET"):
            saved = self.env[name]
            self.env[name] = ""
            result = self.run_script("balance.sh")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing environment variable: " + name, result.stderr)
            self.env[name] = saved


if __name__ == "__main__":
    unittest.main()
