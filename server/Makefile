VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install run test clean

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

run: install
	$(PYTHON) app.py

test: install
	$(PYTHON) -m pytest

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
