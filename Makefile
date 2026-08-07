.PHONY: help up down logs ps clean
COMPOSE := docker compose
help:
	@echo "make up - spustí všetky služby"
	@echo "make down - zastaví všetky služby"
	@echo "make logs - zobrazí logy"
	@echo "make ps - zobrazí stav"
	@echo "make clean - zastaví a vymaže dáta"
up:
	$(COMPOSE) up -d
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f
ps:
	$(COMPOSE) ps
clean:
	$(COMPOSE) down -v
