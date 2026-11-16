#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/_common.sh"
if [[ $# != 1 ]]; then
    printf 'Usage: bash curl/check-call.sh EXTERNAL_ID\n' >&2
    exit 1
fi
request GET "/integrations/call-requests/$(encode_id "$1")"
