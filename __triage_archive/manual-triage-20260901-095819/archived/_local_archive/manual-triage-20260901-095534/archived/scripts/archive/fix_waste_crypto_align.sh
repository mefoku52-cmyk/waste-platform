#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "============================================================"
echo " WASTE PLATFORM - CRYPTOGRAPHY ALIGNMENT"
echo "============================================================"

PYTHON="$(command -v python)"
PIP="$PYTHON -m pip"

echo
echo "[1] AKTUÁLNY STAV"
echo "Python: $($PYTHON --version)"
$PIP show cryptography pyOpenSSL python-jose 2>/dev/null \
  | grep -E '^(Name|Version|Location):' || true

echo
echo "[2] TEST CRYPTOGRAPHY"
$PYTHON - <<'PY'
try:
    import cryptography
    print("cryptography:", cryptography.__version__)

    from cryptography.hazmat.bindings._rust import exceptions
    print("_rust binding: OK")

    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    f = Fernet(key)

    plaintext = b"WASTE PLATFORM CRYPTO ALIGN TEST"
    token = f.encrypt(plaintext)
    result = f.decrypt(token)

    if result != plaintext:
        raise RuntimeError("plaintext mismatch")

    print("Encryption: OK")
    print("Decryption: OK")
    print("CRYPTOGRAPHY RUNTIME: OK")

except Exception as e:
    print("CRYPTOGRAPHY RUNTIME: FAIL")
    print(repr(e))
    raise SystemExit(20)
PY

CRYPTO_STATUS=$?

if [ "$CRYPTO_STATUS" -ne 0 ]; then
    echo
    echo "CRITICAL: cryptography runtime nefunguje."
    exit "$CRYPTO_STATUS"
fi

echo
echo "[3] PYOPENSSL KONTROLA"

$PYTHON - <<'PY'
try:
    import OpenSSL
    print("pyOpenSSL:", OpenSSL.__version__)

    from OpenSSL import SSL
    print("OpenSSL.SSL import: OK")

except Exception as e:
    print("pyOpenSSL: FAIL")
    print(repr(e))
    raise SystemExit(21)
PY

OPENSSL_STATUS=$?

echo
echo "[4] PYTHON-JOSE KONTROLA"

$PYTHON - <<'PY'
try:
    import jose
    print("python-jose:", getattr(jose, "__version__", "unknown"))

    from jose import jwt
    print("python-jose JWT import: OK")

except Exception as e:
    print("python-jose: FAIL")
    print(repr(e))
    raise SystemExit(22)
PY

JOSE_STATUS=$?

echo
echo "============================================================"
echo " [5] PIP CHECK"
echo "============================================================"

$PIP check || true

echo
echo "============================================================"
echo " [6] FINÁLNY STAV"
echo "============================================================"

$PIP show cryptography pyOpenSSL python-jose 2>/dev/null \
  | grep -E '^(Name|Version|Location):' || true

echo
echo "============================================================"

if [ "$CRYPTO_STATUS" -eq 0 ] && \
   [ "$OPENSSL_STATUS" -eq 0 ] && \
   [ "$JOSE_STATUS" -eq 0 ]; then

    echo " CRYPTO STACK RUNTIME: OK"
    echo " cryptography: FUNGUJE"
    echo " pyOpenSSL: FUNGUJE"
    echo " python-jose: FUNGUJE"
    echo "============================================================"
    exit 0
else
    echo " CRYPTO STACK: PARTIAL / FAIL"
    echo "============================================================"
    echo "cryptography status: $CRYPTO_STATUS"
    echo "pyOpenSSL status:    $OPENSSL_STATUS"
    echo "python-jose status:  $JOSE_STATUS"
    exit 1
fi
