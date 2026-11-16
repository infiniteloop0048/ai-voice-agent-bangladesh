"""Run hourly with a JSON export of local orders: id, status, created_at."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sworborno import Sworborno


def main():
    client = Sworborno()
    if len(sys.argv) != 2:
        raise RuntimeError("Usage: python3 python/reconcile.py path/to/orders.json")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    for order in json.loads(Path(sys.argv[1]).read_text()):
        if order["status"] != "awaiting_confirmation":
            continue
        created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
        if created.tzinfo is None:
            raise ValueError("created_at must include a timezone")
        if created >= cutoff:
            continue
        result = client.get_call(order["id"])
        if result.get("outcome") is not None or result.get("status") == "failed":
            # Feed these results to your order update code; old failed rows need review.
            print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
