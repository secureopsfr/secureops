.PHONY: install test lint
install:
	pip install -e ".[dev]"
test:
	pytest -q -ra
lint:
	black --check --config pyproject.toml .
	isort --check-only --profile black .
	flake8 --config .flake8 .
