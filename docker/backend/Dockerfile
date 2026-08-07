FROM python:3.11-slim

WORKDIR /app

# Inštalácia systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopírovanie requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírovanie kódu
COPY backend/ .

# Vytvorenie užívateľa
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Spustenie
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
