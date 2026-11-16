#!/usr/bin/env bash
set -euo pipefail

for name in VOICE_API_URL VOICE_API_KEY VOICE_WEBHOOK_SECRET; do
    if [[ -z "${!name:-}" ]]; then
        printf 'Missing environment variable: %s\n' "$name" >&2
        exit 1
    fi
done

# Keep a guide sample here so this file can also be copied on its own.
if [[ $# -gt 0 ]]; then
    payload=$(cat -- "$1")
else
    payload=$(cat <<'JSON'
{
  "external_id": "10432",
  "phone": "01798XXXXXX",
  "context": {
    "customer_name": "Rahim Uddin",
    "order_id": "10432",
    "total": 1450,
    "payment_method": "cod",
    "address": "House 12, Road 4, Dhanmondi, Dhaka",
    "items": [
      { "name": "Cotton Shirt", "qty": 2, "price": 650 },
      { "name": "Delivery", "qty": 1, "price": 150 }
    ]
  }
}
JSON
)
fi

response_body=$(mktemp)
response_headers=$(mktemp)
trap 'rm -f "$response_body" "$response_headers"' EXIT
if ! status=$(curl --silent --show-error --connect-timeout 10 --max-time 10 \
    -X POST "${VOICE_API_URL%/}/integrations/call-requests" \
    -H "Authorization: Bearer $VOICE_API_KEY" -H 'Content-Type: application/json' \
    --data-binary "$payload" --dump-header "$response_headers" \
    --output "$response_body" --write-out '%{http_code}'); then
    printf 'HTTP %s: request failed or timed out\n' "${status:-000}" >&2
    body=$(cat "$response_body")
    printf '%s\n' "${body//"$VOICE_API_KEY"/'[redacted]'}" >&2
    exit 1
fi
if [[ ! "$status" =~ ^2[0-9][0-9]$ ]]; then
    body=$(cat "$response_body")
    printf 'HTTP %s: %s\n' "$status" "${body//"$VOICE_API_KEY"/'[redacted]'}" >&2
    exit 1
fi
printf 'HTTP %s\n' "$status" >&2
cat "$response_body"
