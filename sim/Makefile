PYTHON   ?= python3
OUT      ?= captures.csv

SERVER   ?= http://localhost:8080
NUM_NODES ?= 3
SPACING  ?= 10
BEHAVIOR ?= wander
SPEED    ?= 1.0
MAC      ?= aa:aa:aa:aa:aa:01
INTERVAL ?= 1.0

.DEFAULT_GOAL := help
.PHONY: help run parse clean

help: ## Show this help
	@echo "sim/ Makefile"
	@echo ""
	@echo "Usage: make <target> [VAR=value ...] -- see README.md for details"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'
	@echo ""
	@echo "Current settings: SERVER=$(SERVER) NUM_NODES=$(NUM_NODES) SPACING=$(SPACING) \
BEHAVIOR=$(BEHAVIOR) SPEED=$(SPEED) MAC=$(MAC) INTERVAL=$(INTERVAL) OUT=$(OUT)"

run: ## Run the node simulator (SERVER, NUM_NODES, SPACING, BEHAVIOR, SPEED, MAC, INTERVAL)
	$(PYTHON) treasure.py --server $(SERVER) --num-nodes $(NUM_NODES) \
		--node-spacing $(SPACING) --behavior $(BEHAVIOR) --speed $(SPEED) \
		--mac $(MAC) --interval $(INTERVAL)

parse: ## Parse serial capture logs (LOGS=glob, required) into a CSV (OUT=path)
	$(PYTHON) parse_captures.py $(LOGS) -o $(OUT)

clean: ## Remove the generated CSV and __pycache__
	rm -rf __pycache__ $(OUT)
