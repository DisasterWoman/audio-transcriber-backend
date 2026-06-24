.PHONY: dev test lint format check migrate ci

dev:
	.venv/bin/fastapi dev app/main.py

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .

check:
	.venv/bin/ruff check .
	.venv/bin/pytest

migrate:
	.venv/bin/alembic upgrade head

ci:
	.venv/bin/ruff check .
	.venv/bin/alembic upgrade head
	.venv/bin/pytest
