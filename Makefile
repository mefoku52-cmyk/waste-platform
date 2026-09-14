# =============================================================================
# CMEP Platform — Professional Makefile
# =============================================================================

.PHONY: help install install-dev dev dev-worker dev-beat test test-unit test-integration test-cov lint format format-check migrate migrate-create db-upgrade db-downgrade db-reset up down ps logs logs-api monitor-up monitor-down audit audit-security clean clean-all

# --- Default ---
help:	## Zobrazi napovedu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Environment ---
install:	## Instaluje produkcne zavislosti
	pip install -r requirements.txt

install-dev:	## Instaluje dev zavislosti
	pip install -e ".[dev,test]"

# --- Development ---
dev:	## Spusti backend v dev mode (auto-reload)
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-worker:	## Spusti Celery worker
	celery -A app.worker worker -l info

dev-beat:	## Spusti Celery beat (scheduler)
	celery -A app.worker beat -l info

# --- Testing ---
test:	## Spusti vsetky testy
	pytest tests -v

test-unit:	## Spusti unit testy
	pytest app/tests/unit -v -m unit

test-integration:	## Spusti integration testy
	pytest app/tests/integration -v -m integration

test-cov:	## Spusti testy s coverage reportom
	pytest tests --cov=app --cov-report=html --cov-report=term

# --- Code Quality ---
lint:	## Spusti linting (flake8 + mypy)
	flake8 app --max-line-length=100 --extend-ignore=E203,W503
	mypy app

format:	## Formatuje kod (black + isort)
	black app
	isort app

format-check:	## Kontrola formatovania bez zmeny
	black --check app
	isort --check-only app

# --- Database ---
migrate:	## Vytvori a aplikuje Alembic migracie
	alembic revision --autogenerate -m "auto_migration"
	alembic upgrade head

migrate-create:	## Vytvori novu migraciu (manualny nazov)
	@read -p "Nazov migracie: " name; \
	alembic revision --autogenerate -m "$$name"

db-upgrade:	## Aplikuje migracie
	alembic upgrade head

db-downgrade:	## Vrati poslednu migraciu
	alembic downgrade -1

db-reset:	## Resetuje databazu (POZOR: maze data!)
	alembic downgrade base
	alembic upgrade head

# --- Docker ---
up:	## Spusti vsetky sluzby v Dockeri
	docker compose up -d --build

down:	## Zastavi Docker sluzby
	docker compose down

ps:	## Stav Docker sluzieb
	docker compose ps

logs:	## Logy zo vsetkych sluzieb
	docker compose logs -f

logs-api:	## Logy iba z API
	docker compose logs -f api

# --- Monitoring ---
monitor-up:	## Spusti monitoring stack
	docker compose -f docker-compose.monitoring.yml up -d

monitor-down:	## Zastavi monitoring stack
	docker compose -f docker-compose.monitoring.yml down

# --- Security Audit ---
audit:	## Forenzny audit projektu
	bash scripts/forensic-audit.sh

audit-security:	## Kontrola hardcoded secretov
	@grep -rn "password\|secret\|token\|api_key" app/ --include="*.py" | grep -v ".pyc" | grep -v "test" || echo "Ziadne obvious secrety v kode (skontroluj .env!)"

# --- Cleanup ---
clean:	## Vycisti cache, pyc, logy
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

clean-all: clean	## Vycisti aj Docker volumes (POZOR!)
	docker compose down -v
	docker system prune -f

prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
