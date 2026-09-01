#!/data/data/com.termux/files/usr/bin/bash

PYTHON="$(command -v python)"
PYLIB="/data/data/com.termux/files/usr/lib/libpython3.14.so"
RUST="/data/data/com.termux/files/usr/lib/python3.14/site-packages/cryptography/hazmat/bindings/_rust.abi3.so"

echo "============================================================"
echo " WASTE PLATFORM - CRYPTO ABI FORENSIC"
echo "============================================================"

echo
echo "[1] SYSTEM"
echo "Python:"
echo "$PYTHON"

echo
echo "Python version:"
python --version

echo
echo "Architecture:"
uname -m

echo
echo "Android:"
getprop ro.build.version.release 2>/dev/null || true

echo
echo "ABI:"
getprop ro.product.cpu.abi 2>/dev/null || true

echo
echo "Secondary ABI:"
getprop ro.product.cpu.abilist 2>/dev/null || true

echo
echo "============================================================"
echo " [2] PYTHON CONFIG"
echo "============================================================"

python - <<'PY'
import sys
import sysconfig
import ctypes

print("sys.executable:")
print(sys.executable)

print()
print("sys.prefix:")
print(sys.prefix)

print()
print("Python version:")
print(sys.version)

print()
print("SOABI:")
print(sysconfig.get_config_var("SOABI"))

print()
print("EXT_SUFFIX:")
print(sysconfig.get_config_var("EXT_SUFFIX"))

print()
print("LDLIBRARY:")
print(sysconfig.get_config_var("LDLIBRARY"))

print()
print("LIBDIR:")
print(sysconfig.get_config_var("LIBDIR"))

print()
print("MULTIARCH:")
print(sysconfig.get_config_var("MULTIARCH"))

print()
print("Py_DEBUG:")
print(sysconfig.get_config_var("Py_DEBUG"))

print()
print("WITH_PYMALLOC:")
print(sysconfig.get_config_var("WITH_PYMALLOC"))

print()
print("ctypes python:")
try:
    py = ctypes.PyDLL(None)
    addr = ctypes.cast(
        getattr(py, "PyLong_Type"),
        ctypes.c_void_p
    ).value

    print("PyLong_Type address:", hex(addr))

except Exception as e:
    print("PyLong_Type lookup through process: FAIL")
    print(repr(e))
PY

echo
echo "============================================================"
echo " [3] FILES"
echo "============================================================"

echo
echo "libpython:"
ls -lh "$PYLIB" 2>&1 || true

echo
echo "_rust.abi3.so:"
ls -lh "$RUST" 2>&1 || true

echo
echo "file:"
file "$PYLIB" 2>&1 || true
file "$RUST" 2>&1 || true

echo
echo "============================================================"
echo " [4] LIBPYTHON SYMBOL"
echo "============================================================"

if command -v nm >/dev/null 2>&1; then
    echo
    echo "Searching PyLong_Type in libpython..."

    nm -D "$PYLIB" 2>/dev/null \
        | grep -E 'PyLong_Type|PyType_Type' \
        || echo "NO SYMBOL FOUND"

else
    echo "nm is not installed"
fi

echo
echo "============================================================"
echo " [5] RUST UNDEFINED SYMBOLS"
echo "============================================================"

if command -v readelf >/dev/null 2>&1; then
    readelf -Ws "$RUST" 2>/dev/null \
        | grep -E 'PyLong_Type|UND' \
        | grep -E 'PyLong_Type|UND' \
        | head -100 \
        || true
else
    echo "readelf is not installed"
fi

echo
echo "============================================================"
echo " [6] RUST NEEDED LIBRARIES"
echo "============================================================"

if command -v readelf >/dev/null 2>&1; then
    readelf -d "$RUST" 2>/dev/null \
        | grep -E 'NEEDED|SONAME|RPATH|RUNPATH' \
        || true
fi

echo
echo "============================================================"
echo " [7] LD LIBRARY"
echo "============================================================"

echo "LD_LIBRARY_PATH:"
echo "${LD_LIBRARY_PATH:-<empty>}"

echo
echo "LD_PRELOAD:"
echo "${LD_PRELOAD:-<empty>}"

echo
echo "============================================================"
echo " [8] CRYPTOGRAPHY"
echo "============================================================"

python - <<'PY'
import cryptography
print("cryptography:", cryptography.__version__)
print("location:", cryptography.__file__)

try:
    import cryptography.hazmat.bindings._rust as rust
    print("_rust import: OK")
    print("_rust location:", rust.__file__)
except Exception as e:
    print("_rust import: FAIL")
    print(repr(e))
PY

echo
echo "============================================================"
echo " [9] DIRECT DLOPEN"
echo "============================================================"

python - <<'PY'
import ctypes

PYLIB="/data/data/com.termux/files/usr/lib/libpython3.14.so"
RUST="/data/data/com.termux/files/usr/lib/python3.14/site-packages/cryptography/hazmat/bindings/_rust.abi3.so"

print("Loading libpython with RTLD_GLOBAL...")

try:
    py = ctypes.CDLL(PYLIB, mode=ctypes.RTLD_GLOBAL)
    print("libpython GLOBAL: OK")
except Exception as e:
    print("libpython GLOBAL: FAIL")
    print(repr(e))
    raise SystemExit(1)

print()

print("Loading Rust extension...")

try:
    rust = ctypes.CDLL(RUST, mode=ctypes.RTLD_GLOBAL)
    print("_rust: OK")
except Exception as e:
    print("_rust: FAIL")
    print(repr(e))
PY

echo
echo "============================================================"
echo " DIAGNOSTIKA HOTOVA"
echo "============================================================"
