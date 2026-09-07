#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

fail() {
    printf 'RELEASE_IDENTITY_ERROR: %s\n' "$*" >&2
    exit 2
}

RELEASE_ID="${RELEASE_ID:-}"
IMAGE_TAG="${IMAGE_TAG:-}"

[ -n "$RELEASE_ID" ] || fail "RELEASE_ID is required"
[ -n "$IMAGE_TAG" ] || fail "IMAGE_TAG is required"

case "$RELEASE_ID" in
    latest|dev|test|current)
        fail "forbidden RELEASE_ID"
        ;;
esac

case "$IMAGE_TAG" in
    latest|dev|test|current)
        fail "forbidden IMAGE_TAG"
        ;;
esac

printf '%s' "$RELEASE_ID" | grep -Eq '^[A-Za-z0-9._:/-]+$' || \
    fail "RELEASE_ID contains unsupported characters"

printf '%s' "$IMAGE_TAG" | grep -Eq '^[A-Za-z0-9._:/-]+$' || \
    fail "IMAGE_TAG contains unsupported characters"

printf 'RELEASE_ID_VALID=1\n'
printf 'IMAGE_TAG_VALID=1\n'
exit 0
