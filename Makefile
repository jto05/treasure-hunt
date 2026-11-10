FRONTEND_DIR := frontend
SERVER_DIR   := server

.DEFAULT_GOAL := help
.PHONY: help install run clean

help: ## Show this help
	@echo "treasure-hunt Makefile"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'

install: ## Install frontend dependencies (npm install) -- server deps are handled separately by server/Makefile
	cd $(FRONTEND_DIR) && npm install

run: install ## Run the Flask server and the Vite dev server together (Ctrl+C stops both)
	@( cd $(SERVER_DIR) && make run ) & server_pid=$$!; \
	( cd $(FRONTEND_DIR) && npm run dev ) & frontend_pid=$$!; \
	trap 'kill $$server_pid $$frontend_pid 2>/dev/null' EXIT INT TERM; \
	wait

clean: ## Remove frontend node_modules and build output
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist
