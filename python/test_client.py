import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from sworborno import Sworborno


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "VOICE_API_URL": "https://example.com/api/v1",
            "VOICE_API_KEY": "vk_live_xxxxxxxxxxxxxxxxxxxx",
            "VOICE_WEBHOOK_SECRET": "change-me",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def response(self, status, body):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = status
        response.headers = {}
        response.read.return_value = body
        return response

    @patch("sworborno.build_opener")
    def test_audio_and_queued_job_stay_distinct(self, opener):
        opener.return_value.open.side_effect = [
            self.response(200, b"\x00\xffaudio"),
            self.response(202, b'{"id":"VOICEOVER_ID","status":"queued"}'),
        ]
        client = Sworborno()
        audio = client.voiceover("VOICE_ID", "আপনার অর্ডারটি আজ পাঠানো হয়েছে।")
        queued = client.voiceover("VOICE_ID", "আপনার অর্ডারটি আজ পাঠানো হয়েছে।")
        self.assertEqual(audio.body, b"\x00\xffaudio")
        self.assertEqual(queued.status, 202)
        self.assertEqual(queued.json()["status"], "queued")
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)["text"], "আপনার অর্ডারটি আজ পাঠানো হয়েছে।")
        self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 120)

    @patch("sworborno.build_opener")
    def test_http_error_keeps_status_body_and_hides_key(self, opener):
        key = os.environ["VOICE_API_KEY"]
        opener.return_value.open.side_effect = HTTPError(
            "https://example.com/api/v1/integrations/balance", 401, "Unauthorized", {}, io.BytesIO(("bad " + key).encode())
        )
        with self.assertRaises(RuntimeError) as raised:
            Sworborno().balance()
        self.assertIn("HTTP 401: bad [redacted]", str(raised.exception))
        self.assertNotIn(key, str(raised.exception))
        self.assertEqual(opener.return_value.open.call_count, 1)

    @patch("sworborno.build_opener")
    def test_network_failure_does_not_retry(self, opener):
        opener.return_value.open.side_effect = URLError("offline")
        with self.assertRaisesRegex(RuntimeError, "failed or timed out"):
            Sworborno().balance()
        self.assertEqual(opener.return_value.open.call_count, 1)

    @patch("sworborno.build_opener")
    def test_missing_environment_stops_before_http(self, opener):
        for name in ("VOICE_API_URL", "VOICE_API_KEY", "VOICE_WEBHOOK_SECRET"):
            with self.subTest(name=name), patch.dict(os.environ, {name: ""}):
                with self.assertRaisesRegex(RuntimeError, name):
                    Sworborno()
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
