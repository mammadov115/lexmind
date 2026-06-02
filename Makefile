.PHONY: install run test clean

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -v

clean:
	rm -rf .pytest_cache .venv .ruff_cache build dist *.egg-info lexmind.db
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
