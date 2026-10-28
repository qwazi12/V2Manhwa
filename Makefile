.PHONY: test check-contracts test-media e2e api web infra dev migrate setup
PYTHON ?= .venv/bin/python
setup:
	python3 scripts/setup_local.py
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.lock
	cd web && npm ci
infra:
	docker compose up -d --build
migrate:
	set -a; . ./.env.local; set +a; PYTHONPATH=api .venv/bin/alembic -c api/alembic.ini upgrade head
test:
	PYTHONPATH=api $(PYTHON) -m pytest -q tests
check-contracts:
	$(PYTHON) scripts/validate_contracts.py
test-media:
	$(PYTHON) scripts/test_synthetic_media.py
e2e:
	@echo "Synthetic API/storage integration. Browser smoke steps: ops/PHASE0_LOCAL_RUNBOOK.md."
	PYTHONPATH=api $(PYTHON) -m pytest -q tests/test_demo_api.py
api:
	set -a; . ./.env.local; set +a; PYTHONPATH=api $(PYTHON) -m uvicorn flamingo_next_api.main:app --host 127.0.0.1 --port 8000 --no-access-log
web:
	cd web && npm run dev
dev:
	./start-studio.command
