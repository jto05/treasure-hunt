# esp32-node/

Firmware for the three treasure boards. Each board joins the game's
Wi-Fi network, passively sniffs nearby phones' Wi-Fi signal strength
(RSSI), and reports it to the Pi's game server once a second.

## Prerequisites

### 1. Install `arduino-cli`

```
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```
This installs it to `./bin` in whatever directory you ran the command
from — move it somewhere on your `PATH` (e.g. `sudo mv bin/arduino-cli /usr/local/bin/`)
so `make` can find it. On macOS you can also use `brew install arduino-cli`.

Confirm it's working:
```
arduino-cli version
```

### 2. Install the ESP32 board core

```
arduino-cli core update-index --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core install esp32:esp32 --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
This is what `FQBN = esp32:esp32:esp32` in the `Makefile` refers to —
the board definition this sketch compiles against.

### 3. Install the one external library this sketch needs

```
arduino-cli lib install ArduinoJson
```
`WiFi.h` and `HTTPClient.h` don't need a separate install — they ship
with the ESP32 core you just installed.

## Building and flashing

Everything goes through the `Makefile` in `treasure_node/`:

```
cd treasure_node
make build              # compile only
make upload             # flash a board that's already compiled
make flash              # build + upload + open the serial monitor
make monitor            # just open the serial monitor (Ctrl+C to exit)
make clean              # force a clean rebuild
```

Plug the board in over USB first, find its serial port, and pass it if
it's not `/dev/ttyUSB0` (the Makefile's default):
```
ls /dev/ttyUSB*                 # Linux
ls /dev/cu.*                    # macOS
make flash PORT=/dev/ttyUSB1
```

`make flash` is the one you'll use most — it builds, uploads, and drops
you into the serial monitor so you can immediately see
`Connecting to TreasureHunt...`, the board's own MAC, and then one
`sent=ok tracking=N` line per second once it's reporting.

## Tailoring a board to a node

The same sketch runs on all three boards — what makes each one "node A"
vs "B" vs "C" is three constants at the top of `treasure_node.ino` and
`report.cpp`, set **before you flash that specific board**:

1. **`treasure_node.ino`** — the node letter this board reports as:
   ```cpp
   const char* NODE = "A"; // change to specific node before flashing
   ```
   Change this to `"B"` or `"C"` for the other two boards. This is the
   value that ends up in the `"node"` field of every report sent to the
   server, so get it right before flashing — there's nothing on the
   board itself afterward that visibly shows which letter it was
   flashed with, so keep track of which physical board got which letter
   (e.g. a sticker on the enclosure).

2. **`report.cpp`** — where the server actually is:
   ```cpp
   static const char *REPORT_URL = "http://10.42.0.1:8080/api/report";
   ```
   This is the same for all three boards (they all report to the same
   Pi), but needs to match wherever the server is actually running:
   - Testing against a dev machine: that machine's LAN IP and whatever
     port `make run`/`make serve` is using (default `8080`).
   - The real Pi, running the `treasurehunt-server` systemd service:
     the Pi's IP on `wlan0` (commonly `10.42.0.1` if it's acting as its
     own access point), port `80` (the service's configured port) —
     so just `http://10.42.0.1/api/report`, no `:8080`.

3. **`treasure_node.ino`** — the Wi-Fi network to join, if it's ever
   not `"TreasureHunt"`:
   ```cpp
   const char* WIFI_SSID = "TreasureHunt";
   ```

After changing any of these, re-flash with `make flash` so the board
picks up the new values — they're compiled in, not read at runtime.
