"""Verify bytes before parsing a webhook as JSON."""

import hashlib
import hmac
import time


def verify_signature(raw_body, timestamp, signature, secret, now=None):
    if not timestamp or not signature or not secret:
        return False
    if not timestamp.isascii() or not timestamp.isdigit():
        return False
    try:
        seconds = int(timestamp)
    except ValueError:
        return False
    if abs((time.time() if now is None else now) - seconds) > 300:
        return False
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.encode(), signature.encode())
