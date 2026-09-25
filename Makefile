.PHONY: install venv run test migrate lint format check db-up db-down clean

venv:
	@if [ ! -d "venv" ]; then \
		echo "==> Creating virtual environment..."; \
		python3 -m venv venv; \
	else \
		echo "==> Virtual environment already exists."; \
	fi
	@echo "==> Virtual environment ready."
	@echo "To activate it, run: source venv/bin/activate"

install:
	./scripts/install.sh

run:
	./scripts/run.sh

metrics:
	@curl -sf http://localhost:8000/health >/dev/null || (echo "ERROR: FastAPI is not running. Run 'make run' first."; exit 1)
	open http://localhost:8000/metrics

prometheus:
	@curl -sf http://localhost:8000/health >/dev/null || (echo "ERROR: FastAPI is not running. Run 'make run' first."; exit 1)
	docker compose up -d prometheus
	open http://localhost:9090

test:
	./scripts/test.sh

migrate:
	./venv/bin/python -m alembic upgrade head

lint:
	./venv/bin/python -m ruff check .

format:
	./venv/bin/python -m ruff format .

check:
	./venv/bin/python -m ruff check .
	./venv/bin/python -m pytest -vv --tb=short

db-up:
	docker compose up -d postgres

db-down:
	docker compose stop postgres

clean:
	docker rm -f orc_shack_test_db 2>/dev/null || true
	rm -rf venv
