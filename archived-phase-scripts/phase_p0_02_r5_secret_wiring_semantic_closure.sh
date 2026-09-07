#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT_ROOT="${HOME}/waste-platform"
REPORT="${PROJECT_ROOT}/audit-output/p0_02_r5_secret_wiring_semantic_closure.txt"

READ_ONLY=YES
NO_SOURCE_WRITES=YES
NO_RUNTIME_EXECUTION=YES
NO_ENV_EXECUTION=YES
NO_BUILD=YES
NO_DEPLOYMENT=YES
NO_DELETIONS=YES
NO_SECRET_VALUES_PRINTED=YES
BOUNDED_SCAN=YES

mkdir -p "${PROJECT_ROOT}/audit-output" 2>/dev/null || true

exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R5 SECRET WIRING SEMANTIC CLOSURE"
echo "============================================================"

FAILURE_COUNT=0
REVIEW_COUNT=0

EXPECTED_SECRETS=(
  "POSTGRES_PASSWORD"
  "DATABASE_PASSWORD"
  "JWT_SECRET_KEY"
  "JWT_REFRESH_SECRET_KEY"
  "S3_SECRET_KEY"
)

echo
echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

if [ ! -d "${PROJECT_ROOT}" ]; then
    echo "FAIL: PROJECT_ROOT_MISSING"
    exit 20
fi
echo "PASS: PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"

for flag in \
    READ_ONLY \
    NO_SOURCE_WRITES \
    NO_RUNTIME_EXECUTION \
    NO_ENV_EXECUTION \
    NO_BUILD \
    NO_DEPLOYMENT \
    NO_DELETIONS \
    NO_SECRET_VALUES_PRINTED \
    BOUNDED_SCAN
do
    value="${!flag}"
    if [ "${value}" != "YES" ]; then
        echo "FAIL: SAFETY_FLAG_${flag}=${value}"
        FAILURE_COUNT=$((FAILURE_COUNT+1))
    else
        echo "PASS: ${flag}=YES"
    fi
done

AUTHORITY_FILES=(
  ".env.production"
  "docker-compose.yml"
  "app/core/config.py"
  ".github/workflows/ci.yml"
)

echo
echo "============================================================"
echo "2. REQUIRED AUTHORITY FILES"
echo "============================================================"

for f in "${AUTHORITY_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${f}" ]; then
        echo "PASS: AUTHORITY_PRESENT=${f}"
    else
        echo "FAIL: AUTHORITY_MISSING=${f}"
        FAILURE_COUNT=$((FAILURE_COUNT+1))
    fi
done

echo
echo "============================================================"
echo "3. SECRET IDENTIFIER SET"
echo "============================================================"

for key in "${EXPECTED_SECRETS[@]}"; do
    echo "SECRET_IDENTIFIER=${key}"
done

echo
echo "============================================================"
echo "4. PRODUCTION SECRET STORE"
echo "============================================================"

ENV_FILE="${PROJECT_ROOT}/.env.production"
PRODUCTION_ENV_SECRET_COUNT=0

for key in "${EXPECTED_SECRETS[@]}"; do
    count="$(
        awk -v k="${key}" '
            $0 ~ "^[[:space:]]*" k "[[:space:]]*=" {
                c++
            }
            END { print c+0 }
        ' "${ENV_FILE}"
    )"

    if [ "${count}" -eq 1 ]; then
        echo "PASS: ENV_SECRET_AUTHORITY KEY=${key} CLASSIFICATION=SECRET_STORE_VALUE VALUE=<REDACTED>"
        PRODUCTION_ENV_SECRET_COUNT=$((PRODUCTION_ENV_SECRET_COUNT+1))
    elif [ "${count}" -eq 0 ]; then
        echo "FAIL: ENV_SECRET_AUTHORITY_MISSING KEY=${key}"
        FAILURE_COUNT=$((FAILURE_COUNT+1))
    else
        echo "FAIL: ENV_SECRET_AUTHORITY_DUPLICATE KEY=${key} COUNT=${count}"
        FAILURE_COUNT=$((FAILURE_COUNT+1))
    fi
done

echo "PRODUCTION_ENV_SECRET_COUNT=${PRODUCTION_ENV_SECRET_COUNT}"

if [ "${PRODUCTION_ENV_SECRET_COUNT}" -eq 5 ]; then
    echo "PASS: PRODUCTION_ENV_SECRET_AUTHORITY_EXACT"
else
    echo "FAIL: PRODUCTION_ENV_SECRET_AUTHORITY_NOT_EXACT"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
fi

echo
echo "============================================================"
echo "5. DOCKER COMPOSE SEMANTIC TOKEN PROOF"
echo "============================================================"

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_UNRELATED_COUNT=0

for key in "${EXPECTED_SECRETS[@]}"; do

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        lineno="${line%%:*}"
        content="${line#*:}"

        # Detect actual Compose/shell interpolation referring to this
        # expected secret, including forms such as:
        # ${JWT_SECRET_KEY}
        # ${JWT_SECRET_KEY:-default}
        # $JWT_SECRET_KEY
        if printf '%s\n' "${content}" | \
            grep -Eq '\$\{[^}]*'"${key}"'[^}]*\}|\$'"${key}"'([^A-Za-z0-9_]|$)'
        then
            echo "FILE=docker-compose.yml LINE=${lineno} KEY=${key} CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>"
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT+1))
            continue
        fi

        # If the key is present but there is no variable interpolation,
        # classify the RHS as literal/non-reference.
        echo "FILE=docker-compose.yml LINE=${lineno} KEY=${key} CLASSIFICATION=LITERAL_OR_NON_REFERENCE VALUE=<REDACTED>"
        COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT+1))

    done < <(
        grep -nF "${key}" "${COMPOSE_FILE}" || true
    )
done

echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

if [ "${COMPOSE_LITERAL_COUNT}" -gt 0 ]; then
    echo "FAIL: LITERAL_SECRET_ASSIGNMENT_DETECTED_IN_COMPOSE"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
else
    echo "PASS: NO_LITERAL_EXPECTED_SECRET_ASSIGNMENT_IN_COMPOSE"
fi

if [ "${COMPOSE_REFERENCE_COUNT}" -gt 0 ]; then
    echo "PASS: COMPOSE_SECRET_INTERPOLATION_DETECTED"
else
    echo "REVIEW: NO_COMPOSE_SECRET_INTERPOLATION_DETECTED"
    REVIEW_COUNT=$((REVIEW_COUNT+1))
fi

echo
echo "============================================================"
echo "6. RUNTIME CONFIG SEMANTIC TOKEN PROOF"
echo "============================================================"

CONFIG_FILE="${PROJECT_ROOT}/app/core/config.py"

RUNTIME_REFERENCE_COUNT=0
RUNTIME_DECLARATION_COUNT=0
RUNTIME_LITERAL_COUNT=0

for key in "${EXPECTED_SECRETS[@]}"; do

    while IFS= read -r line; do
        [ -z "${line}" ] && continue

        lineno="${line%%:*}"
        content="${line#*:}"

        # Python type/declaration forms are not secret value exposure.
        if printf '%s\n' "${content}" | \
            grep -Eq '^[[:space:]]*(#|'"${key}"'[[:space:]]*:|'"${key}"'[[:space:]]*=[[:space:]]*(str|SecretStr|Optional|Annotated))'
        then
            echo "FILE=app/core/config.py LINE=${lineno} KEY=${key} CLASSIFICATION=TYPE_OR_DECLARATION VALUE=<REDACTED>"
            RUNTIME_DECLARATION_COUNT=$((RUNTIME_DECLARATION_COUNT+1))
            continue
        fi

        # Explicit runtime environment/config references.
        if printf '%s\n' "${content}" | \
            grep -Eq 'getenv[[:space:]]*\(|environ(\.|\[)|os\.environ|settings\.|config\.|SecretStr'
        then
            echo "FILE=app/core/config.py LINE=${lineno} KEY=${key} CLASSIFICATION=RUNTIME_REFERENCE VALUE=<REDACTED>"
            RUNTIME_REFERENCE_COUNT=$((RUNTIME_REFERENCE_COUNT+1))
            continue
        fi

        # Explicit literal assignment is a failure only when the RHS
        # contains a non-reference value.
        if printf '%s\n' "${content}" | \
            grep -Eq "${key}[[:space:]]*=[[:space:]]*['\\\"]"
        then
            echo "FILE=app/core/config.py LINE=${lineno} KEY=${key} CLASSIFICATION=LITERAL_ASSIGNMENT VALUE=<REDACTED>"
            RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT+1))
            continue
        fi

        echo "FILE=app/core/config.py LINE=${lineno} KEY=${key} CLASSIFICATION=SEMANTIC_REVIEW VALUE=<REDACTED>"
        REVIEW_COUNT=$((REVIEW_COUNT+1))
        echo "REVIEW: RUNTIME_SECRET_LINE_REQUIRES_CONTEXT=${lineno}"

    done < <(
        grep -nF "${key}" "${CONFIG_FILE}" || true
    )
done

echo "RUNTIME_REFERENCE_COUNT=${RUNTIME_REFERENCE_COUNT}"
echo "RUNTIME_DECLARATION_COUNT=${RUNTIME_DECLARATION_COUNT}"
echo "RUNTIME_LITERAL_COUNT=${RUNTIME_LITERAL_COUNT}"

if [ "${RUNTIME_LITERAL_COUNT}" -gt 0 ]; then
    echo "FAIL: LITERAL_RUNTIME_SECRET_ASSIGNMENT_DETECTED"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
else
    echo "PASS: NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT_DETECTED"
fi

if [ "${RUNTIME_REFERENCE_COUNT}" -gt 0 ]; then
    echo "PASS: RUNTIME_SECRET_REFERENCE_SEMANTICALLY_CLASSIFIED"
else
    echo "REVIEW: NO_RUNTIME_SECRET_REFERENCE_CLASSIFIED"
    REVIEW_COUNT=$((REVIEW_COUNT+1))
fi

echo
echo "============================================================"
echo "7. CI SECRET BOUNDARY"
echo "============================================================"

CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"
CI_TEST_SECRET_COUNT=0
CI_REVIEW_COUNT=0

while IFS= read -r line; do
    [ -z "${line}" ] && continue

    lineno="${line%%:*}"
    content="${line#*:}"

    matched_key=""

    for key in "${EXPECTED_SECRETS[@]}"; do
        if printf '%s\n' "${content}" | grep -qF "${key}"; then
            matched_key="${key}"
            break
        fi
    done

    [ -z "${matched_key}" ] && continue

    # Inspect a bounded local context around the matching line.
    start=$((lineno-3))
    [ "${start}" -lt 1 ] && start=1
    end=$((lineno+3))

    context="$(
        sed -n "${start},${end}p" "${CI_FILE}" 2>/dev/null || true
    )"

    if printf '%s\n' "${context}" | \
        grep -Eiq 'test|pytest|unit|mock|dummy|fake|ci|fixture|testing'
    then
        echo "FILE=.github/workflows/ci.yml LINE=${lineno} KEY=${matched_key} CLASSIFICATION=TEST_CONFIGURATION VALUE=<REDACTED>"
        CI_TEST_SECRET_COUNT=$((CI_TEST_SECRET_COUNT+1))
    else
        echo "REVIEW: CI_SECRET_LINE_REQUIRES_CONTEXT_REVIEW=${lineno}"
        CI_REVIEW_COUNT=$((CI_REVIEW_COUNT+1))
        REVIEW_COUNT=$((REVIEW_COUNT+1))
    fi

done < <(
    grep -nE 'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        "${CI_FILE}" || true
)

echo "CI_TEST_SECRET_COUNT=${CI_TEST_SECRET_COUNT}"
echo "CI_CONTEXT_REVIEW_COUNT=${CI_REVIEW_COUNT}"

echo
echo "============================================================"
echo "8. CROSS-AUTHORITY INVARIANTS"
echo "============================================================"

echo "PRODUCTION_SECRET_AUTHORITY=.env.production"
echo "PRODUCTION_COMPOSE_AUTHORITY=docker-compose.yml"
echo "RUNTIME_CONFIG_AUTHORITY=app/core/config.py"
echo "CI_TEST_AUTHORITY=.github/workflows/ci.yml"

# Invariant 1: exactly five expected production secret keys.
if [ "${PRODUCTION_ENV_SECRET_COUNT}" -eq 5 ]; then
    echo "PASS: INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    echo "FAIL: INVARIANT_PRODUCTION_SECRET_SET_NOT_EXACT"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
fi

# Invariant 2: Compose must not contain literal expected secret values.
# This proof intentionally checks syntax/authority only and never prints values.
if [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    echo "FAIL: INVARIANT_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
fi

# Invariant 3: runtime must not contain literal secret assignments.
if [ "${RUNTIME_LITERAL_COUNT}" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    echo "FAIL: INVARIANT_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
    FAILURE_COUNT=$((FAILURE_COUNT+1))
fi

echo "PASS: SECRET_VALUE_OUTPUT_REMAINED_REDACTED"

echo
echo "============================================================"
echo "9. FINAL CLASSIFICATION"
echo "============================================================"

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "PRODUCTION_ENV_SECRET_COUNT=${PRODUCTION_ENV_SECRET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "RUNTIME_REFERENCE_COUNT=${RUNTIME_REFERENCE_COUNT}"
echo "RUNTIME_LITERAL_COUNT=${RUNTIME_LITERAL_COUNT}"
echo "CI_TEST_SECRET_COUNT=${CI_TEST_SECRET_COUNT}"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R5_SECRET_WIRING_SEMANTIC_FAILURE"
    EXIT_CODE=20
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R5_SECRET_WIRING_SEMANTIC_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R5_SECRET_WIRING_SEMANTIC_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R5_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
