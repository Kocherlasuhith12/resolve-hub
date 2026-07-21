.PHONY: install dev workers format lint typecheck test test-unit test-integration test-auth test-search test-phase4 migrate migration up down logs frontend-install frontend-dev frontend-lint frontend-build frontend-test frontend-e2e

install:
	python3.12 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

dev:
	.venv/bin/uvicorn resolvehub.app.main:app --reload

workers:
	docker compose up -d temporal-worker sla-orchestrator outbox-worker

format:
	.venv/bin/ruff format .

lint:
	.venv/bin/ruff format --check .
	.venv/bin/ruff check .

typecheck:
	.venv/bin/mypy resolvehub tests

test:
	.venv/bin/coverage run -m pytest
	.venv/bin/coverage report

test-unit:
	.venv/bin/pytest tests/unit

test-integration:
	.venv/bin/pytest -m integration

test-auth:
	.venv/bin/pytest tests/unit/test_identity.py tests/integration/test_phase1_api.py

test-search:
	.venv/bin/pytest tests/unit/test_search_service.py tests/integration/test_phase4_search_ai.py

test-phase4:
	.venv/bin/pytest tests/unit/test_search_service.py tests/unit/test_ai_provider.py tests/integration/test_phase4_search_ai.py

migrate:
	.venv/bin/alembic upgrade head

migration:
	.venv/bin/alembic revision --autogenerate -m "$(message)"

up:
	docker compose up -d postgres redis mailpit temporal

down:
	docker compose down

logs:
	docker compose logs -f api postgres redis temporal temporal-worker sla-orchestrator outbox-worker

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

frontend-e2e:
	cd frontend && npm run test:e2e
