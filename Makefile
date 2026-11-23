FRONTEND_DIR := frontend
SERVER_DIR   := server

MAC ?= aa:bb:cc:dd:ee:ff
FAKE_LEASES_FILE := /tmp/treasurehunt-fake.leases
FLASK_PORT := 8080
VITE_PORT  := 5173

.DEFAULT_GOAL := help
.PHONY: help install run run-flask run-vite run-flask-fake clean

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
	@( $(MAKE) run-flask ) & server_pid=$$!; \
	( $(MAKE) run-vite ) & frontend_pid=$$!; \
	trap 'kill $$server_pid $$frontend_pid 2>/dev/null; \
	      lsof -ti:$(FLASK_PORT) -sTCP:LISTEN | xargs -r kill 2>/dev/null; \
	      lsof -ti:$(VITE_PORT) -sTCP:LISTEN | xargs -r kill 2>/dev/null' EXIT INT TERM; \
	wait

run-flask: ## Run only the Flask backend (server/, port 8080)
	cd $(SERVER_DIR) && $(MAKE) run

run-flask-fake: ## Run Flask with a fake DHCP lease for IP=<client-ip> (optional MAC=<mac>, defaults to aa:bb:cc:dd:ee:ff) -- for testing when there's no real DHCP/ESP32 setup, e.g. over SSH to a dev server. Usage: make run-flask-fake IP=10.0.0.5
ifndef IP
	$(error IP is required, e.g. make run-flask-fake IP=10.0.0.5 -- check the Flask log line "no mac found for ip ..." to find the right value)
endif
	@echo "9999999999 $(MAC) $(IP) testdevice *" > $(FAKE_LEASES_FILE)
	cd $(SERVER_DIR) && LEASES_PATH=$(FAKE_LEASES_FILE) $(MAKE) run

run-vite: install ## Run only the Vite frontend dev server (frontend/, port 5173)
	cd $(FRONTEND_DIR) && npm run dev -- --host

clean: ## Remove frontend node_modules and build output
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist
