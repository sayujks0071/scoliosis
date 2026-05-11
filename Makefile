.PHONY: help install smoke test build clean

PYTHON := .venv/bin/python3
ifeq ($(wildcard $(PYTHON)),)
PYTHON := python3
endif

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make install  - install the editable package plus test/doc dependencies' \
		'  make smoke    - run a quick import/version sanity check' \
		'  make test     - run the core pytest subset used for local validation' \
		'  make build    - build a wheel into dist/' \
		'  make clean    - remove common build and test artifacts'

install:
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install -r requirements.txt

smoke:
	$(PYTHON) -c "import spinalmodes; print(spinalmodes.__version__)"
	$(PYTHON) -m spinalmodes.cli version

test:
	$(PYTHON) -m pytest -q tests/test_cli.py tests/test_smoke.py tests/test_minimal_experiment_script.py tests/test_generate_spine_daily_update.py

build:
	$(PYTHON) -m pip install build
	$(PYTHON) -m build --wheel

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov
