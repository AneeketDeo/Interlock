.PHONY: up down logs test lint typecheck clean deploy-gcp fe-dev fe-build

# ── Infrastructure (Docker Compose) ──────────────────────────────────
# Note: On Windows PowerShell without make, run: docker compose up -d --build
up:
	docker compose up -d --build
	@echo "✓ RCA-Sentinel is running"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API:      http://localhost:8000/docs"
	@echo "  MCP:      http://localhost:8001"

down:
	docker compose down -v

logs:
	docker compose logs -f

# ── Google Cloud Platform ───────────────────────────────────────────
deploy-gcp:
	bash scripts/deploy_gcp.sh

# ── Backend Code Quality & Testing (uv) ─────────────────────────────
# Note: On Windows PowerShell without make, run: cd backend && uv run pytest -v
test:
	cd backend && uv run pytest tests/ -v --tb=short

test-cov:
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	cd backend && uv run ruff check app/ tests/
	cd backend && uv run ruff format --check app/ tests/

format:
	cd backend && uv run ruff check --fix app/ tests/
	cd backend && uv run ruff format app/ tests/

typecheck:
	cd backend && uv run mypy app/

check: lint typecheck test
	@echo "✓ All checks passed"

# ── Frontend (npm) ──────────────────────────────────────────────────
fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build

fe-test:
	cd frontend && npm run test

fe-lint:
	cd frontend && npm run lint

# ── Housekeeping ────────────────────────────────────────────────────
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
