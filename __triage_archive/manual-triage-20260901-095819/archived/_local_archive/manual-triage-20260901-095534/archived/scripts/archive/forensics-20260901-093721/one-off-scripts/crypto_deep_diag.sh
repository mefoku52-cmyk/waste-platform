#!/data/data/com.termux/files/usr/bin/bash

set -u

PY="$(command -v python)"
PYVER="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
LIBPY="$PREFIX/lib/libpython${PYVER}.so"
RUST="$PREFIX/lib/python${PYVER}/site-packages/cryptography/hazmat/bindings/_rust.abi3.so"

echo "============================================================"
echo " WASTE PLATFORM - CRYPTO DEEP DIAGNOSTIC"
echo "============================================================"

echo
echo "[1] SYSTEM"
uname -a
echo "Android:"
getprop ro.build.version.release 2>/dev/null || true
echo "ABI:"
getprop ro.product.cpu.abi 2>/dev/null || true
echo "PREFIX:"
echo "$PREFIX"

echo
echo "[2] PYTHON"
"$PY" --version
echo "Executable:"
echo "$PY"
echo "SOABI:"
"$PY" -c 'import sysconfig; print(sysconfig.get_config_var("SOABI"))'
echo "EXT_SUFFIX:"
"$PY" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))'

echo
echo "[3] LIBPYTHON"
echo "$LIBPY"

ls -lh "$LIBPY"

echo
echo "PyLong_Type:"
nm -D "$LIBPY" 2>/dev/null | grep ' PyLong_Type$' || true

echo
echo "PyType_Type:"
nm -D "$LIBPY" 2>/dev/null | grep ' PyType_Type$' || true

echo
echo "[4] RUST EXTENSION"
echo "$RUST"

ls -lh "$RUST"

echo
echo "ELF:"
file "$RUST"

echo
echo "[5] PYTHON SYMBOLS REQUIRED BY RUST"

readelf -Ws "$RUST" 2>/dev/null |
awk '$7 == "UND" && $8 ~ /^Py/ {print $8}' |
sort -u |
head -100

echo
echo "[6] PYTHON SYMBOLS PROVIDED BY LIBPYTHON"

for sym in \
    PyLong_Type \
    PyType_Type \
    PyModule_Type \
    PyUnicode_Type \
    PyBytes_Type \
    PyExc_TypeError \
    PyExc_ValueError \
    PyObject_CallNoArgs \
    PyObject_Vectorcall \
    PyImport_Import
do
    printf "%-35s " "$sym"

    if nm -D "$LIBPY" 2>/dev/null |
       grep -q " $sym$"; then
        echo "PROVIDED"
    else
        echo "MISSING"
    fi
done

echo
echo "[7] PYTHON BUILD CONFIG"

"$PY" - <<'PY'
import sys
import sysconfig

print("version:", sys.version)
print("implementation:", sys.implementation)
print("SOABI:", sysconfig.get_config_var("SOABI"))
print("MULTIARCH:", sysconfig.get_config_var("MULTIARCH"))
print("LDLIBRARY:", sysconfig.get_config_var("LDLIBRARY"))
print("LIBDIR:", sysconfig.get_config_var("LIBDIR"))
print("Py_ENABLE_SHARED:", sysconfig.get_config_var("Py_ENABLE_SHARED"))
print("CONFIG_ARGS:", sysconfig.get_config_var("CONFIG_ARGS"))
PY

echo
echo "[8] CRYPTOGRAPHY METADATA"

"$PY" -m pip show cryptography pyOpenSSL python-jose 2>/dev/null |
grep -E '^(Name|Version|Location):' || true

echo
echo "[9] OPENSSL"

openssl version -a 2>/dev/null | head -20 || true

echo
echo "[10] CRYPTOGRAPHY RUST DEPENDENCIES"

readelf -d "$RUST" 2>/dev/null |
grep -E 'NEEDED|RUNPATH|RPATH' || true

echo
echo "[11] RUST RELOCATION / SYMBOL TABLE"

readelf -Ws "$RUST" 2>/dev/null |
grep -E 'PyLong_Type|PyType_Type|PyObject|PyExc_' |
head -80

echo
echo "[12] DIRECT IMPORT"

"$PY" - <<'PY'
import sys
print("Python:", sys.version)

try:
    import cryptography
    print("cryptography:", cryptography.__version__)
except Exception as e:
    print("cryptography import FAIL:", repr(e))

try:
    from cryptography.hazmat.bindings._rust import exceptions
    print("_rust: OK")
except Exception as e:
    print("_rust: FAIL")
    print(type(e).__name__ + ":", str(e))
    print("repr:", repr(e))

try:
    import ctypes

    lib = ctypes.CDLL(
        sys.prefix + "/lib/libpython"
        + f"{sys.version_info.major}.{sys.version_info.minor}.so",
        mode=ctypes.RTLD_GLOBAL
    )

    print("libpython RTLD_GLOBAL: OK")

    addr = ctypes.cast(
        getattr(lib, "PyLong_Type"),
        ctypes.c_void_p
    ).value

    print("PyLong_Type runtime address:", hex(addr))

except Exception as e:
    print("ctypes PyLong_Type test FAIL:", repr(e))

print()
print("DIAGNOSTIKA DOKONČENÁ")
PY

echo
echo "============================================================"
echo " END"
echo "============================================================"
