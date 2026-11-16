import json
from pathlib import Path
import unittest

from signature import verify_signature


class SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vector = json.loads((Path(__file__).resolve().parents[1] / "payloads/signature-vector.json").read_text())

    def verify(self, body=None, timestamp=None, signature=None, now=None):
        v = self.vector
        return verify_signature(
            v["body"].encode() if body is None else body,
            v["timestamp"] if timestamp is None else timestamp,
            v["signature"] if signature is None else signature,
            v["secret"], int(v["timestamp"]) if now is None else now,
        )

    def test_shared_vector(self):
        self.assertTrue(self.verify())

    def test_changed_body(self):
        self.assertFalse(self.verify(body=self.vector["body"].encode() + b" "))

    def test_changed_timestamp(self):
        self.assertFalse(self.verify(timestamp=str(int(self.vector["timestamp"]) + 1)))

    def test_old_timestamp(self):
        self.assertFalse(self.verify(now=int(self.vector["timestamp"]) + 301))

    def test_future_timestamp(self):
        self.assertFalse(self.verify(now=int(self.vector["timestamp"]) - 301))

    def test_missing_signature(self):
        self.assertFalse(self.verify(signature=""))

    def test_missing_timestamp(self):
        self.assertFalse(self.verify(timestamp=""))

    def test_invalid_timestamp(self):
        self.assertFalse(self.verify(timestamp="invalid"))

    def test_window_boundary(self):
        self.assertTrue(self.verify(now=int(self.vector["timestamp"]) + 300))


if __name__ == "__main__":
    unittest.main()
