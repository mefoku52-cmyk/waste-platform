#!/data/data/com.termux/files/usr/bin/bash
set -u

BASE="$HOME/waste-platform/cmep_ai_architektura"
SOURCE="$BASE/05_bezpecnost_a_schvalovanie.sh"
RUNNER="$BASE/05_spustenie_auditu.sh"

if [ ! -f "$SOURCE" ]; then
    echo "STOP: Povodny skript neexistuje."
    exit 1
fi

if [ -e "$RUNNER" ]; then
    echo "STOP: Spustaci skript uz existuje. Nic neprepisujem."
    exit 1
fi

sed '/if \[ -e "\$BASE\/05_bezpecnost_a_schvalovanie\.sh" \]; then/,/^[[:space:]]*fi$/d' \
    "$SOURCE" > "$RUNNER"

if [ ! -s "$RUNNER" ]; then
    echo "STOP: Spustaci skript je prazdny."
    exit 1
fi

bash -n "$RUNNER" || exit 1
chmod 700 "$RUNNER"

echo "=== SPUSTENIE DAVKY 05 ==="
bash "$RUNNER"
