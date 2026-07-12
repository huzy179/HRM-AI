SHELL := /bin/sh

COMPOSE ?= docker compose
API_URL ?= http://localhost:8000
OLLAMA_CHAT_MODEL ?= llama3
OLLAMA_EMBED_MODEL ?= nomic-embed-text
PYTEST ?= pytest

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "\nHRM-AI commands:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: up
up: ## Build and start the full Docker stack
	$(COMPOSE) up -d --build

.PHONY: up-logs
up-logs: ## Build, start, and follow logs
	$(COMPOSE) up --build

.PHONY: down
down: ## Stop containers
	$(COMPOSE) down

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE) restart

.PHONY: ps
ps: ## Show container status
	$(COMPOSE) ps

.PHONY: logs
logs: ## Follow logs for the main app services
	$(COMPOSE) logs -f api frontend worker_parse worker_index worker_llm

.PHONY: logs-all
logs-all: ## Follow logs for all services
	$(COMPOSE) logs -f

.PHONY: logs-observe
logs-observe: ## Follow observability logs
	$(COMPOSE) logs -f prometheus grafana loki promtail jaeger

.PHONY: migrate
migrate: ## Run Alembic migrations in the API container
	$(COMPOSE) exec api alembic upgrade head

.PHONY: models
models: ## Pull required Ollama models
	$(COMPOSE) exec ollama ollama pull $(OLLAMA_EMBED_MODEL)
	$(COMPOSE) exec ollama ollama pull $(OLLAMA_CHAT_MODEL)

.PHONY: seed-users
seed-users: ## Create/update local test users in the API container
	$(COMPOSE) exec api env PYTHONPATH=. python scripts/seed_test_users.py

.PHONY: setup
setup: up migrate models seed-users ## Start stack, migrate DB, pull Ollama models, and seed test users

.PHONY: health
health: ## Check API health
	curl -fsS $(API_URL)/health
	@printf "\n"

.PHONY: metrics
metrics: ## Check metrics summary
	curl -fsS $(API_URL)/metrics/summary
	@printf "\n"

.PHONY: workers
workers: ## Check queue and worker health
	curl -fsS $(API_URL)/admin/workers
	@printf "\n"

.PHONY: test
test: ## Run backend tests locally
	PYTHONPATH=. $(PYTEST)

.PHONY: test-api
test-api: ## Run API contract and endpoint tests locally
	PYTHONPATH=. $(PYTEST) tests/test_api_contract.py tests/test_metrics_endpoint.py tests/test_admin_queues_workers.py

.PHONY: test-docker
test-docker: ## Run tests inside the API container
	$(COMPOSE) exec api python -m pytest

.PHONY: ragas-venv
ragas-venv: ## Create local eval virtualenv and install Ragas dependencies
	python3 -m venv .venv-evals
	. .venv-evals/bin/activate && pip install -r backend/requirements.txt -r evals/requirements.txt

.PHONY: ragas
ragas: ## Run Policy RAG Ragas eval using .venv-evals
	. .venv-evals/bin/activate && python evals/ragas_policy_eval.py --input evals/policy_eval_questions.jsonl

.PHONY: frontend-lint
frontend-lint: ## Run frontend lint locally
	cd frontend && npm run lint

.PHONY: compose-config
compose-config: ## Validate docker-compose.yml
	$(COMPOSE) config

.PHONY: pull
pull: ## Pull service images
	$(COMPOSE) pull

.PHONY: legacy-worker
legacy-worker: ## Start legacy all-in-one worker profile
	$(COMPOSE) --profile legacy up -d --build worker

.PHONY: urls
urls: ## Print local service URLs
	@printf "Frontend:    http://localhost:3000\n"
	@printf "API docs:    http://localhost:8000/docs\n"
	@printf "API health:  http://localhost:8000/health\n"
	@printf "Prometheus:  http://localhost:9090\n"
	@printf "Grafana:     http://localhost:3001  admin/admin\n"
	@printf "Loki:        http://localhost:3100\n"
	@printf "Jaeger:      http://localhost:16686\n"
