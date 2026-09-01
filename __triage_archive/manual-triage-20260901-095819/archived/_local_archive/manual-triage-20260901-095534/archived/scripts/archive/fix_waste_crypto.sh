#!/data/data/com.termux/files/usr/bin/bash

set -u

echo "============================================================"
echo " WASTE PLATFORM - CRYPTO DIAGNOSTIKA"
echo "============================================================"

echo
echo "[1] PYTHON"
python --version
python -m pip --version

echo
echo "[2] BALIKY"
python -m pip show cryptography pyOpenSSL python-jose 2>/dev/null \
    | grep -E '^(Name|Version):' || true

echo
echo "[3] PIP CHECK"
python -m pip check || true

echo
echo "============================================================"
echo " CRYPTOGRAPHY TEST"
echo "============================================================"

python - <<'PY'
import sys

print("Python:", sys.version)
print()

# ------------------------------------------------------------
# cryptography
# ------------------------------------------------------------

try:
    import cryptography
    print("[1] cryptography import: OK")
    print("    Version:", cryptography.__version__)
except Exception as e:
    print("[1] cryptography import: FAIL")
    print("   ", repr(e))
    raise SystemExit(10)

print()

# ------------------------------------------------------------
# Rust binding
# ------------------------------------------------------------

try:
    from cryptography.hazmat.bindings._rust import exceptions
    print("[2] Rust binding: OK")
except Exception as e:
    print("[2] Rust binding: FAIL")
    print("   ", repr(e))
    raise SystemExit(20)

print()

# ------------------------------------------------------------
# Fernet
# ------------------------------------------------------------

try:
    from cryptography.fernet import Fernet
    print("[3] Fernet import: OK")
except Exception as e:
    print("[3] Fernet import: FAIL")
    print("   ", repr(e))
    raise SystemExit(30)

print()

# ------------------------------------------------------------
# Encryption
# ------------------------------------------------------------

try:
    key = Fernet.generate_key()
    f = Fernet(key)

    plaintext = b"WASTE PLATFORM CRYPTO TEST"

    token = f.encrypt(plaintext)

    print("[4] Encryption: OK")
    print("    Token length:", len(token))

except Exception as e:
    print("[4] Encryption: FAIL")
    print("   ", repr(e))
    raise SystemExit(40)

print()

# ------------------------------------------------------------
# Decryption
# ------------------------------------------------------------

try:
    result = f.decrypt(token)

    if result != plaintext:
        print("[5] Decryption: FAIL")
        print("    Plaintext mismatch")
        raise SystemExit(50)

    print("[5] Decryption: OK")
    print("    Result:", result.decode())

except Exception as e:
    print("[5] Decryption: FAIL")
    print("   ", repr(e))
    raise SystemExit(50)

print()
print("============================================================")
print(" VYSLEDOK: CRYPTOGRAPHY FUNGUJE")
print("============================================================")
PY

STATUS=$?

echo
echo "============================================================"
echo " FINAL"
echo "============================================================"

echo
echo "[6] PIP CHECK"
python -m pip check || true

echo
echo "[7] INSTALLED VERSIONS"
python -m pip show cryptography pyOpenSSL python-jose 2>/dev/null \
    | grep -E '^(Name|Version):' || true

echo

if [ "$STATUS" -eq 0 ]; then
    echo "============================================================"
    echo " OK - CRYPTOGRAPHY JE FUNKCNA"
    echo "============================================================"
else
    echo "============================================================"
    echo " FAIL - CRYPTOGRAPHY STALE NIE JE FUNKCNA"
    echo " EXIT CODE: $STATUS"
    echo "============================================================"
fi

exit "$STATUS"
