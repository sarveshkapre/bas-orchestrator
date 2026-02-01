PYTHON ?= python3

.PHONY: setup dev test lint typecheck build check release

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && python -m pip install -U pip
	. .venv/bin/activate && pip install -e .[dev]

DEV_ARGS ?=

dev:
	. .venv/bin/activate && bas --help

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check .
	. .venv/bin/activate && ruff format --check .

typecheck:
	. .venv/bin/activate && mypy src tests

build:
	. .venv/bin/activate && $(PYTHON) -m build

check: lint typecheck test

release:
	@echo "Run docs/RELEASE.md checklist"
