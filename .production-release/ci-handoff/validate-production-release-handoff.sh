#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

: "${RELEASE_ID:?RELEASE_ID is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

case "$RELEASE_ID" in
    latest|dev|test|current)
        printf '%s\n' "FORBIDDEN_RELEASE_ID" >&2
        exit 2
        ;;
esac

case "$IMAGE_TAG" in
    latest|dev|test|current)
        printf '%s\n' "FORBIDDEN_IMAGE_TAG" >&2
        exit 2
        ;;
esac

case "$RELEASE_ID" in
    *[!A-Za-z0-9._:/+-]*)
        printf '%s\n' "INVALID_RELEASE_ID" >&2
        exit 2
        ;;
esac

case "$IMAGE_TAG" in
    *[!A-Za-z0-9._:/+-]*)
        printf '%s\n' "INVALID_IMAGE_TAG" >&2
        exit 2
        ;;
esac

printf 'RELEASE_HANDOFF_VALID=1\n'
exit 0
