VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
SYSTEM_PYTHON ?= python3.12

.PHONY: install test lint download-data profile ingest transform quality metrics emissions analytics dashboard clean

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
	$(PYTHON) -m campus_utility.ingestion

transform:
	$(PYTHON) -m campus_utility.transformations

quality:
	$(PYTHON) -m campus_utility.quality

metrics:
	$(PYTHON) -m campus_utility.metrics

emissions:
	$(PYTHON) -m campus_utility.emissions

analytics:
	$(PYTHON) -m campus_utility.analytics

dashboard:
	$(VENV)/bin/streamlit run dashboard/app.py

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov
