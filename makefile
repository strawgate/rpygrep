


lint:
	ruff format
	ruff check --fix

test:
	pytest tests

sync:
	uv sync

all: lint test sync




