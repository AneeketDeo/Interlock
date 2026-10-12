.PHONY: up down seed test lint typecheck clean logs

# ── Infrastructure ──────────────────────────────────────────────────
up:
	docker compose up -d --build
	@echo "✓ RCA-Sentinel is running"
	@echo "  API:      http://localhost:8000/docs"
	@echo "  MCP:      http://localhost:8001"
	@echo "  Frontend: http://localhost:5173"

down:
	docker compose down -v

logs:
	docker compose logs -f

# ── Data ────────────────────────────────────────────────────────────
seed:
	docker compose exec api python -m app.cli seed

replay:
	docker compose exec api python -m app.cli replay

# ── Quality ─────────────────────────────────────────────────────────
lint:
	cd backend && uv run ruff check app/ tests/
	cd backend && uv run ruff format --check app/ tests/

format:
	cd backend && uv run ruff check --fix app/ tests/
	cd backend && uv run ruff format app/ tests/

typecheck:
	cd backend && uv run mypy app/

test:
	cd backend && uv run pytest tests/ -v --tb=short

test-cov:
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing

# ── Frontend ────────────────────────────────────────────────────────
fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build

fe-test:
	cd frontend && npm run test

fe-lint:
	cd frontend && npm run lint

# ── Full pipeline ───────────────────────────────────────────────────
check: lint typecheck test
	@echo "✓ All checks passed"

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
