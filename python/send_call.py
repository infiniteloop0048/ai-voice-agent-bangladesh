import json
import sys
from pathlib import Path

from sworborno import Sworborno


def main():
    client = Sworborno()
    payload = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "payloads/call-request.json"
    print(json.dumps(client.send_call(json.loads(payload.read_text())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
