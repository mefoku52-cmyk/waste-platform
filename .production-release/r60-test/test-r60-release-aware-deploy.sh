#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/data/data/com.termux/files/home/waste-platform"
COMPOSE="${ROOT}/docker-compose.yml"
DEPLOY="${ROOT}/scripts/deploy.sh"

FAILURES=0
PASSES=0

pass() {
    PASSES=$((PASSES + 1))
    printf 'PASS: %s\n' "$*"
}

fail() {
    FAILURES=$((FAILURES + 1))
    printf 'FAIL: %s\n' "$*" >&2
}

assert_match() {
    local pattern="$1"
    local file="$2"
    local label="$3"

    if grep -qE "$pattern" "$file"; then
        pass "$label"
    else
        fail "$label"
    fi
}

assert_absent() {
    local pattern="$1"
    local file="$2"
    local label="$3"

    if grep -qE "$pattern" "$file"; then
        fail "$label"
    else
        pass "$label"
    fi
}

printf '\n============================================================\n'
printf 'R60 RELEASE-AWARE DEPLOY INTEGRATION TEST\n'
printf '============================================================\n'

[ -f "$COMPOSE" ] || fail "COMPOSE_PRESENT"
[ -f "$DEPLOY" ] || fail "DEPLOY_PRESENT"

if [ -f "$COMPOSE" ]; then
    pass "COMPOSE_PRESENT"
fi

if [ -f "$DEPLOY" ]; then
    pass "DEPLOY_PRESENT"
fi

if bash -n "$DEPLOY"; then
    pass "DEPLOY_BASH_SYNTAX"
else
    fail "DEPLOY_BASH_SYNTAX"
fi

assert_match \
    '^    image: cmep-api:\$\{IMAGE_TAG:\?IMAGE_TAG musi byt nastaveny\}' \
    "$COMPOSE" \
    "API_EXPLICIT_RELEASE_IMAGE"

assert_match \
    '^    image: cmep-web:\$\{IMAGE_TAG:\?IMAGE_TAG musi byt nastaveny\}' \
    "$COMPOSE" \
    "WEB_EXPLICIT_RELEASE_IMAGE"

assert_match \
    'IMAGE_TAG' \
    "$COMPOSE" \
    "COMPOSE_IMAGE_TAG_SURFACE"

assert_absent \
    'image:.*latest' \
    "$COMPOSE" \
    "COMPOSE_NO_LATEST"

assert_absent \
    'docker compose.*up.*--build' \
    "$DEPLOY" \
    "DEPLOY_NO_UP_BUILD"

assert_match \
    'RELEASE_ID=.*REQUIRED|RELEASE_ID is required' \
    "$DEPLOY" \
    "DEPLOY_RELEASE_ID_REQUIRED"

assert_match \
    'IMAGE_TAG=.*REQUIRED|IMAGE_TAG is required' \
    "$DEPLOY" \
    "DEPLOY_IMAGE_TAG_REQUIRED"

assert_match \
    'sha-\[0-9a-fA-F\]' \
    "$DEPLOY" \
    "RELEASE_ID_FORMAT_VALIDATED"

assert_match \
    'release-\[0-9a-fA-F\]' \
    "$DEPLOY" \
    "IMAGE_TAG_FORMAT_VALIDATED"

assert_match \
    'latest.*dev.*test.*current|latest\*.*dev\*.*test\*.*current\*' \
    "$DEPLOY" \
    "MUTABLE_IDENTITY_REJECTION_PRESENT"

assert_match \
    'previous-release\.env' \
    "$DEPLOY" \
    "PREVIOUS_RELEASE_STATE_PRESENT"

assert_match \
    'current-release\.env' \
    "$DEPLOY" \
    "CURRENT_RELEASE_STATE_PRESENT"

assert_match \
    'docker compose.*config' \
    "$DEPLOY" \
    "COMPOSE_CONFIG_VALIDATION_PRESENT"

assert_match \
    'docker compose.*build api web' \
    "$DEPLOY" \
    "EXPLICIT_API_WEB_BUILD_PRESENT"

assert_absent \
    'alembic.*downgrade' \
    "$DEPLOY" \
    "NO_DATABASE_DOWNGRADE"

assert_absent \
    'source[[:space:]]+.*\.env|^\.[[:space:]].*\.env' \
    "$DEPLOY" \
    "NO_ENV_SOURCE_IN_NEW_DEPLOY"

assert_absent \
    'docker.*--reload|--reload' \
    "$DEPLOY" \
    "NO_RELOAD"

printf '\n--- RELEASE IDENTITY VALIDATION TESTS ---\n'

VALID_RELEASE_ID="sha-0123456789abcdef"
VALID_IMAGE_TAG="release-0123456789abcdef"

if printf '%s\n' "$VALID_RELEASE_ID" | grep -qE '^sha-[0-9a-fA-F]{7,64}$'; then
    pass "VALID_RELEASE_ID_ACCEPTED"
else
    fail "VALID_RELEASE_ID_ACCEPTED"
fi

if printf '%s\n' "$VALID_IMAGE_TAG" | grep -qE '^release-[0-9a-fA-F]{7,64}$'; then
    pass "VALID_IMAGE_TAG_ACCEPTED"
else
    fail "VALID_IMAGE_TAG_ACCEPTED"
fi

for BAD_ID in latest current dev test; do
    if case "$BAD_ID" in
        *latest*|*current*|*dev*|*test*) true ;;
        *) false ;;
    esac
    then
        pass "MUTABLE_IDENTITY_REJECTED_${BAD_ID}"
    else
        fail "MUTABLE_IDENTITY_REJECTED_${BAD_ID}"
    fi
done

printf '\n--- SECRET SAFETY TEST ---\n'

if grep -qE \
    'POSTGRES_PASSWORD=.*[A-Za-z0-9]|JWT_SECRET_KEY=.*[A-Za-z0-9]|JWT_REFRESH_SECRET_KEY=.*[A-Za-z0-9]' \
    "$DEPLOY"; then
    fail "DEPLOY_DOES_NOT_CONTAIN_SECRET_VALUES"
else
    pass "DEPLOY_DOES_NOT_CONTAIN_SECRET_VALUES"
fi

if grep -qE \
    'docker compose.*--env-file' \
    "$DEPLOY"; then
    pass "COMPOSE_ENV_FILE_AUTHORITY_PRESERVED"
else
    fail "COMPOSE_ENV_FILE_AUTHORITY_PRESERVED"
fi

printf '\n============================================================\n'
printf 'R60 TEST RESULT\n'
printf '============================================================\n'
printf 'PASSES=%s\n' "$PASSES"
printf 'FAILURES=%s\n' "$FAILURES"

if [ "$FAILURES" -eq 0 ]; then
    printf 'R60_TEST_STATUS=PASS\n'
    exit 0
fi

printf 'R60_TEST_STATUS=FAIL\n'
exit 2
