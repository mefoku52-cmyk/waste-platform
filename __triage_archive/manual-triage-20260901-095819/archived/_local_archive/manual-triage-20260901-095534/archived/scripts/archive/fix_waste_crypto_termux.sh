#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "============================================================"
echo " WASTE PLATFORM - CRYPTO RUNTIME FIX"
echo "============================================================"

PYTHON="$(command -v python)"
PYVER="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
LIBPY="$PREFIX/lib/libpython${PYVER}.so"

echo
echo "[1] Python"
echo "Python: $PYTHON"
echo "Version: $("$PYTHON" --version 2>&1)"
echo "PREFIX: $PREFIX"
echo "LIBPY: $LIBPY"

echo
echo "[2] Kontrola libpython"

if [ ! -f "$LIBPY" ]; then
    echo "FAIL: $LIBPY neexistuje"
    exit 10
fi

nm -D "$LIBPY" 2>/dev/null | grep -E ' PyLong_Type$| PyType_Type$' || true

echo
echo "[3] Kontrola cryptography"

"$PYTHON" - <<'PY'
try:
    import cryptography
    print("cryptography:", cryptography.__version__)
    print("location:", cryptography.__file__)
except Exception as e:
    print("cryptography import FAIL:", repr(e))
PY

RUST="$PREFIX/lib/python${PYVER}/site-packages/cryptography/hazmat/bindings/_rust.abi3.so"

echo
echo "[4] Rust extension"
echo "$RUST"

if [ ! -f "$RUST" ]; then
    echo "FAIL: _rust.abi3.so neexistuje"
    exit 11
fi

echo
echo "[5] RPATH/RUNPATH"

readelf -d "$RUST" 2>/dev/null | grep -E 'RPATH|RUNPATH|NEEDED' || true

echo
echo "[6] Termux linker test"

export LD_LIBRARY_PATH="$PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

echo
echo "[7] Python extension test"

"$PYTHON" - <<'PY'
import sys
import ctypes

print("Python:", sys.version)

libpython = ctypes.CDLL(
    sys.prefix + "/lib/libpython"
    + f"{sys.version_info.major}.{sys.version_info.minor}.so",
    mode=ctypes.RTLD_GLOBAL
)

print("libpython RTLD_GLOBAL: OK")

try:
    from cryptography.hazmat.bindings._rust import exceptions
    print("_rust binding: OK")
except Exception as e:
    print("_rust binding: FAIL")
    print(repr(e))
    raise SystemExit(20)

try:
    from cryptography.fernet import Fernet
    print("Fernet import: OK")
except Exception as e:
    print("Fernet import: FAIL")
    print(repr(e))
    raise SystemExit(21)

try:
    plaintext = b"WASTE PLATFORM CRYPTO TEST"
    key = Fernet.generate_key()
    f = Fernet(key)
    token = f.encrypt(plaintext)
    result = f.decrypt(token)

    if result != plaintext:
        print("Encryption/decryption: FAIL")
        raise SystemExit(22)

    print("Encryption: OK")
    print("Decryption: OK")
    print("Result:", result.decode())

except Exception as e:
    print("Crypto operation: FAIL")
    print(repr(e))
    raise SystemExit(23)

print()
print("CRYPTOGRAPHY RUNTIME: OK")
PY

STATUS=$?

echo
echo "============================================================"

if [ "$STATUS" -eq 0 ]; then
    echo " WASTE PLATFORM CRYPTO RUNTIME: OK"
else
    echo " WASTE PLATFORM CRYPTO RUNTIME: FAIL"
    echo " EXIT CODE: $STATUS"
fi

echo "============================================================"

exit "$STATUS"
