FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bezpecnostne minimum: kontajner bezi ako non-root.
RUN useradd -m -u 1000 cmep && chown -R cmep:cmep /app
USER cmep

EXPOSE 8000

# Liveness probe: /health je verejny endpoint bez auth (app/main.py:111).
# Pouziva sa dynamicky PORT (default 8000), rovnako ako CMD nizsie.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:'+os.environ.get('PORT','8000')+'/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
