#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== 1. Installing build dependencies ==="
pkg update -y
pkg install -y rust binutils clang

echo "=== 2. Activating virtual environment ==="
source .venv/bin/activate

echo "=== 3. Uninstalling old cryptography and pyjwt ==="
pip uninstall -y cryptography pyjwt

echo "=== 4. Installing cryptography from source (no binary wheel) ==="
pip install --no-cache-dir --force-reinstall --no-binary cryptography cryptography==41.0.7

echo "=== 5. Installing pyjwt ==="
pip install pyjwt

echo "=== 6. Testing import jwt ==="
python -c "import jwt; print('jwt imported OK')"

echo "=== 7. Testing app.main import ==="
python -c "import app.main; print('app.main imported OK')"

echo "=== 8. Running Alembic migrations ==="
alembic upgrade head

echo "=== All done! You can now run: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload ==="
