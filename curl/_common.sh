#!/usr/bin/env bash
set -euo pipefail

for name in VOICE_API_URL VOICE_API_KEY VOICE_WEBHOOK_SECRET; do
    if [[ -z "${!name:-}" ]]; then
        printf 'Missing environment variable: %s\n' "$name" >&2
        exit 1
    fi
done

encode_id() {
    local value="$1" char encoded='' code
    local LC_ALL=C
    for ((i=0; i<${#value}; i++)); do
        char="${value:i:1}"
        case "$char" in
            [a-zA-Z0-9.~_-]) encoded+="$char" ;;
            *) printf -v code '%%%02X' "'$char"; encoded+="$code" ;;
        esac
    done
    printf '%s' "$encoded"
}

request() {
    local method="$1" path="$2" payload="${3:-}" output="${4:-}" timeout="${5:-10}" status body
    local -a args=()
    response_body=$(mktemp)
    response_headers=$(mktemp)
    trap 'rm -f "$response_body" "$response_headers"' EXIT
    if [[ -n "$payload" ]]; then
        args=(-H 'Content-Type: application/json' --data-binary "@$payload")
    fi
    if ! status=$(curl --silent --show-error --connect-timeout 10 --max-time "$timeout" \
        -X "$method" "${VOICE_API_URL%/}$path" \
        -H "Authorization: Bearer $VOICE_API_KEY" \
        --dump-header "$response_headers" --output "$response_body" \
        --write-out '%{http_code}' "${args[@]}"); then
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
    awk 'tolower($0) ~ /^(content-type|x-voiceover-id|x-audio-seconds|x-charged-seconds):/ {print}' "$response_headers" >&2
    # A queued voiceover is JSON; never save it under an audio filename.
    if [[ -n "$output" ]] && awk 'tolower($0) ~ /^content-type: *audio\// {found=1} END {exit !found}' "$response_headers"; then
        cp "$response_body" "$output"
        printf 'Saved audio to %s\n' "$output" >&2
    else
        cat "$response_body"
    fi
}
