import sys
from threading import Lock

from signature import verify_signature
from sworborno import environment

try:
    _, _, secret = environment()
except RuntimeError as error:
    sys.exit(str(error))

try:
    from flask import Flask, request
except ImportError:
    sys.exit("Flask is required to run this receiver.")

app = Flask(__name__)
receipts = set()
orders = {}
lock = Lock()


@app.post("/webhooks/voice")
def webhook():
    raw = request.get_data(cache=True)
    timestamp = request.headers.get("X-Webhook-Timestamp")
    signature = request.headers.get("X-Signature")
    webhook_id = request.headers.get("X-Webhook-Id")
    if not webhook_id or not verify_signature(raw, timestamp, signature, secret):
        return "Invalid or missing webhook headers", 401
    with lock:
        if webhook_id in receipts:
            return "", 204
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return "Expected a JSON object", 400
        # Production needs a database table and a transaction for the receipt and order update.
        # Keep slow work in a queue so delivery can be acknowledged quickly.
        if data.get("event") == "balance.low":
            app.logger.warning("Voice agent balance low: %s", data.get("balance_minutes"))
        elif data.get("status") == "confirmed":
            address = data.get("address") or {}
            orders[data.get("order_id")] = {
                "status": "confirmed",
                "shipping_thana": address.get("thana"),
                "shipping_zilla": address.get("zilla"),
            }
        else:
            orders[data.get("order_id")] = {
                "status": "needs_review",
                "hold_reason": data.get("reason"),
                "call_note": data.get("summary"),
            }
        receipts.add(webhook_id)
    return "", 204


if __name__ == "__main__":
    app.run()
