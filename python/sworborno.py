"""Small standard-library client. Requests are sent only when a method is called."""

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        # A redirect must not forward the bearer key to another destination.
        return None


def environment():
    names = ("VOICE_API_URL", "VOICE_API_KEY", "VOICE_WEBHOOK_SECRET")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing environment variable(s): " + ", ".join(missing))
    return tuple(os.environ[name] for name in names)


@dataclass
class Response:
    status: int
    headers: object
    body: bytes

    def json(self):
        return json.loads(self.body)


class Sworborno:
    def __init__(self):
        self.url, self.key, self.secret = environment()

    def _request(self, method, path, payload=None, timeout=10):
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        headers = {"Authorization": "Bearer " + self.key}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.url.rstrip("/") + path, data=data, headers=headers, method=method)
        try:
            with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
                body = response.read()
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"HTTP {response.status}: " + body.decode(errors="replace").replace(self.key, "[redacted]"))
                return Response(response.status, response.headers, body)
        except HTTPError as error:
            body = error.read().decode(errors="replace").replace(self.key, "[redacted]")
            raise RuntimeError(f"HTTP {error.code}: {body}") from None
        except (URLError, TimeoutError, OSError):
            raise RuntimeError("HTTP request failed or timed out") from None

    def send_call(self, payload):
        return self._request("POST", "/integrations/call-requests", payload).json()

    def get_call(self, external_id):
        return self._request("GET", "/integrations/call-requests/" + quote(str(external_id), safe="")).json()

    def cancel_call(self, external_id):
        return self._request("DELETE", "/integrations/call-requests/" + quote(str(external_id), safe=""))

    def balance(self):
        return self._request("GET", "/integrations/balance").json()

    def list_voices(self):
        return self._request("GET", "/integrations/tts/voices").json()

    def voiceover(self, voice_id, text, format="mp3"):
        # Keep bytes intact: a short request returns audio, a queued request returns JSON.
        return self._request("POST", "/integrations/tts", {"voice_id": voice_id, "text": text, "format": format}, timeout=120)

    def get_voiceover(self, voiceover_id):
        return self._request("GET", "/integrations/tts/" + quote(str(voiceover_id), safe="")).json()

    def voiceover_audio(self, voiceover_id, format="mp3"):
        return self._request("GET", "/integrations/tts/" + quote(str(voiceover_id), safe="") + "/audio?format=" + quote(format, safe=""), timeout=120)
