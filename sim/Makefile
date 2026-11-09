PYTHON ?= python3
OUT    ?= captures.csv

.DEFAULT_GOAL := help
.PHONY: help parse clean

help: ## Show this help
	@echo "sim/ Makefile"
	@echo ""
	@echo "Usage: make <target> [LOGS=\"~/captures/dist_*.log\"] [OUT=captures.csv]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'
	@echo ""
	@echo "Current settings: OUT=$(OUT)"

parse: ## Parse serial capture logs (LOGS=glob, required) into a CSV (OUT=path)
	$(PYTHON) parse_captures.py $(LOGS) -o $(OUT)

clean: ## Remove the generated CSV and __pycache__
	rm -rf __pycache__ $(OUT)
