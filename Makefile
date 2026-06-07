VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
SYSTEM_PYTHON ?= python3.12

.PHONY: install test lint download-data profile ingest transform quality dashboard clean

install:
	$(SYSTEM_PYTHON) -m venv $(VENV)
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests dashboard

download-data:
	$(VENV)/bin/kaggle datasets download -d cdaclab/unicon -p data/raw --unzip

profile:
	$(PYTHON) -m campus_utility.profiling

ingest:
	@echo "Bronze ingestion workflow will be implemented in Feature 3."

transform:
	@echo "Silver and gold transformation workflow will be implemented in later features."

quality:
	@echo "Data-quality checks will be implemented in Feature 5."

dashboard:
	$(VENV)/bin/streamlit run dashboard/app.py

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov
