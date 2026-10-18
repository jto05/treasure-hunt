FQBN   = esp32:esp32:esp32
PORT   = /dev/ttyUSB0
BAUD   = 115200
SKETCH = .

.DEFAULT_GOAL := help
.PHONY: help build upload monitor flash clean

help: ## Show this help
	@echo "Treasure node Makefile"
	@echo ""
	@echo "Usage: make <target> [PORT=/dev/ttyUSBx]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'
	@echo ""
	@echo "Current settings: FQBN=$(FQBN) PORT=$(PORT) BAUD=$(BAUD)"

build: ## Compile the sketch
	arduino-cli compile --fqbn $(FQBN) $(SKETCH)

upload: ## Flash the compiled sketch to the board
	arduino-cli upload -p $(PORT) --fqbn $(FQBN) $(SKETCH)

monitor: ## Open the serial monitor (Ctrl+C to exit)
	arduino-cli monitor -p $(PORT) -c baudrate=$(BAUD)

flash: build upload monitor ## Build, upload, then open the monitor

clean: ## Force a clean rebuild
	arduino-cli compile --clean --fqbn $(FQBN) $(SKETCH)
