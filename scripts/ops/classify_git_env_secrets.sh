#!/data/data/com.termux/files/usr/bin/bash

echo "============================================================"
echo " WASTE PLATFORM - SECRET VALUE CLASSIFICATION"
echo "============================================================"

echo
echo "=== REPO ==="
git rev-parse --show-toplevel

echo
echo "=== ENV FILE CLASSIFICATION ==="

git ls-files -z |
while IFS= read -r -d '' f; do

    case "$f" in
        .env|.env.*|*/.env|*/.env.*)

            echo
            echo "----- $f -----"

            awk '
            /^[[:space:]]*#/ { next }
            /^[[:space:]]*$/ { next }

            /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/ {

                eq = index($0, "=")

                key = substr($0, 1, eq - 1)
                value = substr($0, eq + 1)

                gsub(/[[:space:]]/, "", key)
                gsub(/^[[:space:]]+/, "", value)
                gsub(/[[:space:]]+$/, "", value)

                classification = "POTENTIAL REAL VALUE"

                if (value == "") {
                    classification = "PLACEHOLDER/EMPTY"
                }

                if (value ~ /^<.*>$/) {
                    classification = "PLACEHOLDER/REDACTED"
                }

                if (value ~ /^\$\{.*\}$/) {
                    classification = "PLACEHOLDER/TEMPLATE"
                }

                if (value == "CHANGE_ME" ||
                    value == "CHANGEME" ||
                    value == "REPLACE_ME" ||
                    value == "YOUR_VALUE" ||
                    value == "YOUR_SECRET" ||
                    value == "placeholder" ||
                    value == "PLACEHOLDER" ||
                    value == "TODO" ||
                    value == "FIXME" ||
                    value == "xxx" ||
                    value == "XXX") {
                    classification = "PLACEHOLDER"
                }

                if (value == "true" ||
                    value == "false" ||
                    value == "null" ||
                    value == "none" ||
                    value == "localhost" ||
                    value == "127.0.0.1" ||
                    value ~ /^[0-9]+$/ ||
                    value ~ /^https?:\/\/localhost/) {
                    classification = "NON-SECRET-LIKE"
                }

                print key " => " classification
            }
            ' "$f"

            ;;
    esac

done

echo
echo "=== SECRET-LIKE TRACKED FILES ==="

git ls-files |
grep -Ei '(^|/)(\.env|.*secret.*|.*credential.*|.*password.*|.*token.*|.*private.*)' |
sort -u

echo
echo "=== UNREACHABLE COMMIT ==="

git show --no-patch \
    --format='%H%n%ad%n%an%n%s' \
    15803461fbebf22bea8dbd3e7dd320a13f5d40bb \
    2>/dev/null || true

echo
echo "============================================================"
echo " CLASSIFICATION HOTOVÁ"
echo "============================================================"
