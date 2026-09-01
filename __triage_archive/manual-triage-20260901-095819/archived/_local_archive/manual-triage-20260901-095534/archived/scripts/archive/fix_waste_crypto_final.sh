#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "============================================================"
echo " WASTE PLATFORM - CRYPTOGRAPHY FINAL FIX"
echo "============================================================"

PY="$(command -v python)"
PIP="$PY -m pip"

echo
echo "[1] Aktuálny stav"
python --version
$PIP --version
$PIP show cryptography 2>/dev/null | grep -E '^(Name|Version|Location):' || true

echo
echo "[2] Záloha package metadát"
BACKUP="$HOME/waste-platform-crypto-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"

cp -a \
  "$PREFIX/lib/python3.14/site-packages/cryptography" \
  "$BACKUP/" 2>/dev/null || true

cp -a \
  "$PREFIX/lib/python3.14/site-packages/cryptography-"*.dist-info \
  "$BACKUP/" 2>/dev/null || true

echo "Backup: $BACKUP"

echo
echo "[3] Odstránenie poškodenej cryptography"
$PIP uninstall -y cryptography

echo
echo "[4] Vyčistenie pip cache"
$PIP cache purge || true

echo
echo "[5] Kontrola Termux balíka"
pkg update -y
pkg install -y openssl python

echo
echo "[6] Inštalácia cryptography bez starej binárky"

# Najprv skúsime verziu kompatibilnú s aktuálnym prostredím.
# --no-cache-dir zabráni opätovnému použitiu starej wheel.
$PIP install --no-cache-dir --force-reinstall "cryptography<49"

STATUS=$?

echo
echo "============================================================"
echo " [7] RUNTIME TEST"
echo "============================================================"

if [ "$STATUS" -ne 0 ]; then
    echo "Inštalácia cryptography zlyhala."
    exit "$STATUS"
fi

python <<'PY'
import sys

print("Python:", sys.version)

try:
    import cryptography
    print("cryptography:", cryptography.__version__)
except Exception as e:
    print("cryptography import FAIL:", repr(e))
    raise SystemExit(20)

try:
    from cryptography.hazmat.bindings._rust import exceptions
    print("_rust binding: OK")
except Exception as e:
    print("_rust binding: FAIL")
    print(repr(e))
    raise SystemExit(21)

try:
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    f = Fernet(key)

    plaintext = b"WASTE PLATFORM CRYPTO TEST"

    token = f.encrypt(plaintext)
    print("Encryption: OK")

    result = f.decrypt(token)

    if result != plaintext:
        print("Decryption: FAIL - plaintext mismatch")
        raise SystemExit(22)

    print("Decryption: OK")
    print("Result:", result.decode())

except Exception as e:
    print("Crypto runtime: FAIL")
    print(repr(e))
    raise SystemExit(23)

print()
print("CRYPTOGRAPHY RUNTIME: OK")
PY

STATUS=$?

echo
echo "============================================================"
echo " [8] PIP CHECK"
echo "============================================================"

$PIP check || true

echo
echo "============================================================"
echo " [9] FINÁLNY STAV"
echo "============================================================"

$PIP show cryptography pyOpenSSL python-jose 2>/dev/null \
    | grep -E '^(Name|Version|Location):' || true

echo
echo "============================================================"

if [ "$STATUS" -eq 0 ]; then
    echo " OK - CRYPTOGRAPHY FUNGUJE"
    echo "============================================================"
    echo
    echo "Backup:"
    echo "  $BACKUP"
    exit 0
else
    echo " FAIL - CRYPTOGRAPHY STÁLE NEFUNGUJE"
    echo " EXIT CODE: $STATUS"
    echo "============================================================"
    echo
    echo "Backup:"
    echo "  $BACKUP"
    exit "$STATUS"
fi
