#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/_common.sh"
case "${1:-}" in
    voices) request GET /integrations/tts/voices ;;
    create)
        if [[ $# -lt 2 ]]; then
            printf 'Usage: bash curl/voiceover.sh create REQUEST_JSON [OUTPUT_AUDIO]\n' >&2
            exit 1
        fi
        request POST /integrations/tts "$2" "${3:-voiceover.mp3}" 120
        ;;
    status)
        if [[ $# != 2 ]]; then
            printf 'Usage: bash curl/voiceover.sh status VOICEOVER_ID\n' >&2
            exit 1
        fi
        request GET "/integrations/tts/$(encode_id "$2")"
        ;;
    audio)
        if [[ $# -lt 2 ]]; then
            printf 'Usage: bash curl/voiceover.sh audio VOICEOVER_ID [mp3|wav] [OUTPUT_AUDIO]\n' >&2
            exit 1
        fi
        format="${3:-mp3}"
        if [[ "$format" != mp3 && "$format" != wav ]]; then
            printf 'Choose mp3 or wav.\n' >&2
            exit 1
        fi
        request GET "/integrations/tts/$(encode_id "$2")/audio?format=$format" '' "${4:-voiceover.$format}" 120
        ;;
    *)
        printf 'Usage: bash curl/voiceover.sh voices|create|status|audio [arguments]\n' >&2
        exit 1
        ;;
esac
