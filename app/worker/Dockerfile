# ============================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /srv/app

RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /srv/app
USER appuser

CMD ["python", "-m", "app.worker.main"]