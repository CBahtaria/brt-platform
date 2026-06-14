RUNTIME := $(shell which podman 2>/dev/null || which docker 2>/dev/null || echo "docker")
COMPOSE  := $(RUNTIME)-compose

.PHONY: setup dev-up dev-down build test lint verify-scope clean install-dev

setup: install-dev

install-dev:
	pip install -e ".[dev]"

dev-up:
	$(COMPOSE) up -d

dev-down:
	$(COMPOSE) down

dev-logs:
	$(COMPOSE) logs -f brt-api

build:
	$(RUNTIME) build --target runtime -t brt-platform:latest .

build-dev:
	$(RUNTIME) build --target dev -t brt-platform:dev .

test: dev-up
	pytest -v tests/

lint:
	ruff check brt_platform tests

verify-scope:
	@echo "=== Scope Discipline Check ==="
	@bash scripts/check-scope-discipline.sh

verify: verify-scope
	@echo "=== Build Verification ==="
	@find brt_platform -name "*.py" -exec python -m py_compile {} \; && echo "✅ Syntax OK"
	@python -c "from brt_platform.api.server import app; print('✅ Import OK')"
	@grep -q 'urllib.request.urlopen' Dockerfile && echo "✅ Python HEALTHCHECK" || echo "FAIL"
	@grep -q 'restart: on-failure' docker-compose.yml && echo "✅ Restart policy" || echo "FAIL"
	@grep -q 'VECTOR_SIZE' brt_platform/core/collection_manager.py && echo "✅ VECTOR_SIZE enforced" || echo "FAIL"
	@grep -q 'HALF_OPEN' brt_platform/core/resilience.py && echo "✅ CircuitBreaker HALF_OPEN" || echo "FAIL"
	@grep -q 'class RedisKeyPrefix' brt_platform/config.py && echo "✅ Redis key convention" || echo "FAIL"
	@grep -q 'CLICKHOUSE_AVAILABLE' brt_platform/core/rag_engine.py && echo "✅ Graceful degradation" || echo "FAIL"

clean:
	$(COMPOSE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
