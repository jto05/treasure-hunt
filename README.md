# Wi‑Fi Treasure Hunt

A 3‑treasure scavenger hunt. Phones get live hot/cold hints over Wi‑Fi. At each treasure, the team plays a **proximity minigame** (move to the right distance and hold it), and completing all three wins.

- **One Raspberry Pi 3 B+** is the base station: it runs the Wi‑Fi network, the game server and **all** game logic, in Python/Flask.
- **Three ESP32 boards** are the hidden treasures. They are dumb sensors: they overhear phones' Wi‑Fi packets, average the signal strength (RSSI) per MAC, and POST it to the Pi every second.
- **Phones** only display. Each team uses one phone with a web page served by the Pi.

This README carries the project's decisions and context so far, so all four team members start from the same picture. Each person owns and writes their own layer; see **Team roles and jobs**.

---

## Decisions since the original project plan

The plan PDF (Sep 23) is still the source of truth for the overall design. These later decisions override it:

| Topic | Plan said | Now |
|---|---|---|
| Server | Python / Flask / waitress | **Same: Python / Flask / waitress.** (A Go server was tried briefly and dropped because only one team member knows Go. Its logic is ported, not reused.) |
| Server code shape | `app.py` + modules | Game logic in a plain Python package with **no Flask imports**; `app.py` is a thin layer of routes. |
| Frontend | Plain HTML/CSS/JS, fixed screen list | **Open.** Lives in its own `web/` folder, talks to the server only through the API. Flask serves it from the same address. |
| Minigames | Riddle / memory / quiz, typed answers | **Proximity minigames**: after finding a treasure, the team must reach and hold a specific distance zone (or pattern of zones). Checked by the server from live signal readings; no typed answers. Which game goes at which treasure is still open. |
| Network stack | NetworkManager hotspot (`nmcli`) | **hostapd** (access point) + **dnsmasq** (DHCP + DNS). NetworkManager leaves `wlan0` alone. |
| Wi‑Fi security | WPA2, password `findme123` | **Open network, no password.** WPA2 lines kept commented out in `hostapd.conf`. |
| ESP32 join | `WiFi.begin(SSID, PASS)` | `WiFi.begin("TreasureHunt")` with no password. |
| DHCP leases path | `/var/lib/NetworkManager/…` | `/var/lib/misc/dnsmasq.leases` |
| Development without hardware | `mock.py` with fake rising/falling readings | **Docker Compose simulation** of the Pi's network, the three treasures and several phones (see **Development with Docker**). |
| Production | Pi | **Same: plain Pi, no Docker.** systemd service + Python virtual environment, plus a backup SD card image. |
| Pi OS | Raspberry Pi OS Lite | Raspberry Pi OS Lite **(64‑bit)**, hostname `huntbase`, Wi‑Fi left blank in Imager, setup over Ethernet. |

Unchanged: 2.4 GHz only, **channel 6** fixed, Pi at **`10.42.0.1`**, all game rules on the server.

---

## Current status

**Done**

- Pi flashed (64‑bit Lite, `huntbase`, SSH).
- `pi-setup/`: `hostapd.conf`, `dnsmasq-treasurehunt.conf`, `treasurehunt-ip.service` (gives `wlan0` its address), `setup.sh`. The open TreasureHunt network broadcasts and a PC can see it.
- A Go server skeleton from an earlier chat. **It's being replaced by Flask**, but it's a useful reference: proximity (stale checks, median, bands, trend, found rule), IP → MAC lookup, captive‑portal probes, atomic state saving, round‑robin orders, and tests for all of these port almost line for line.

**In progress**

**Not started**

- Flask server, frontend, proximity minigames, admin page, `/board`, Docker simulation, ESP32 sketch.
- `treasurehunt-server.service` still points at the Go binary; it needs switching to Flask/waitress (see **Production on the Pi**).

---

## Repo layout

```
treasure-hunt/
  README.md
  docker-compose.yml              development only
  pi-setup/                       Person 1: network + service setup (run on the Pi)
    hostapd.conf
    dnsmasq-treasurehunt.conf
    treasurehunt-ip.service
    treasurehunt-server.service
    setup.sh
  server/                         Person 3: Flask game server
    app.py                        create_app(): routes, cookies, admin PIN, captive probes, serves web/
    hunt/                         game logic, no Flask imports
      config.py                   load config.json + overrides.json
      state.py                    Game, Team, node readings, one lock, atomic save
      proximity.py                smoothing, bands, trend, found rule
      progression.py              orders, completion, win, leaderboard
      netinfo.py                  Person 1: IP -> MAC, connected devices
      challenges/                 proximity minigame types (one file per type)
        __init__.py               registry
        base.py                   Challenge base class
        tbd.py                    placeholder type
    tests/                        pytest
    config.json                   thresholds, treasure MACs, challenge settings, admin PIN
    requirements.txt              pinned; used by the Pi, laptops and Docker alike
    Dockerfile                    development image
  web/                            Person 4 (player page, /board) and Person 1 (admin/): frontend, approach open
    admin/
  sim/                            Person 2: development simulation (Docker)
    world.yaml                    treasure positions, phone paths, path-loss settings
    world.py                      keeps phone positions, turns distance into RSSI
    treasure.py                   simulated ESP32: posts the real report format
    phone.py                      simulated team: registers, polls, walks, plays minigames
    Dockerfile
  esp32-node/                     Person 2: firmware
    treasure_node/treasure_node.ino
```

If the frontend ends up with a build step, its source stays in `web/` and Flask serves the built folder (set with `WEB_DIR`).

---

## Rules for all code

- **Game logic has no Flask imports.** Modules in `server/hunt/` take plain Python values and return results, so they're easy to unit test. `app.py` handlers only parse the request, call into `hunt`, and return JSON.
- **One lock** guards all game state. Waitress serves requests on several threads.
- **Save state** to `state.json` on every change: write a temp file, flush, `os.replace`.
- **Time:** the Pi has no clock battery and no internet. Game times are measured from game start, never wall‑clock dates. Use one injectable `now()` so tests control time.
- **Team identity = cookie** (`team`, random token, `HttpOnly`, `SameSite=Lax`, 24 h). **Location = MAC**, looked up fresh from the request IP on every request, since phones can reconnect with a new address.
- **Ignore readings for the three `treasure_macs`**; treasures overhear each other.
- **Frontend: approach open, but** it loads nothing from the internet, stays small (aim under ~200 KB, the Pi 3 serves every phone), works over plain HTTP, and talks to the server only through the API contracts.
- **`requirements.txt` is the single list of Python packages**, with pinned versions, for the Pi, laptops and Docker.

---

## How the game plays

1. Team joins the open **TreasureHunt** Wi‑Fi.
2. They scan a QR code that opens `http://10.42.0.1`.
3. They enter a team name. The server sets the cookie and assigns a treasure order (the 6 permutations of A/B/C, handed out round‑robin, so teams spread out).
4. The page shows a hot/cold hint for the **current target only**: freezing, cool, warm, hot or burning, plus a trend.
5. When the smoothed signal at that treasure stays at or above its `found` threshold for 3 s, the treasure is **found**.
6. The team taps **Start challenge** and plays that treasure's proximity minigame, for example "back away until you're *warm* and hold it for 5 seconds." The page shows the goal and live progress; the server decides when it's done.
7. Minigame complete → short celebration, hint switches to the next target.
8. Third treasure complete → win screen with finish time and place.

---

## Interface contracts

Shared by the ESP32 firmware, the simulation, the server and the frontend. Change them only with the whole team's agreement.

All JSON. Errors are a 4xx status with `{"error": "<code>"}`. Admin calls send the PIN in an `X-Admin-Pin` header.

| Method and path | Called by | Purpose |
|---|---|---|
| `POST /api/report` | ESP32 / simulated treasure | Signal readings from one treasure |
| `POST /api/team` | Player page | Register; sets the team cookie |
| `GET /api/state` | Player page | Everything the page needs to draw itself, including minigame progress |
| `GET /api/challenge/{node}` | Player page | Description of that treasure's minigame, once found |
| `POST /api/challenge/{node}/start` | Player page | Start the minigame |
| `POST /api/codeword/{node}` | Player page | Optional hidden code word |
| `GET /api/leaderboard` | Player page, `/board` | Rankings |
| `GET /api/admin/status` | Admin page | Nodes, live readings, teams |
| `POST /api/admin/game` | Admin page | `start`, `pause` or `reset` |
| `POST /api/admin/config` | Admin page | Change thresholds and minigame settings live |
| `POST /api/admin/complete` | Admin page | Manually complete a team's current treasure |
| `GET /generate_204`, `/hotspot-detect.html`, etc. | Phones | Captive‑portal probes |

### ESP32 → Pi, every 1 s

```json
POST /api/report
{
  "node": "B",
  "uptime_ms": 523000,
  "readings": {
    "a4:5e:60:12:34:56": {"rssi": -58, "n": 14, "age_ms": 200},
    "3c:22:fb:ab:cd:ef": {"rssi": -71, "n": 3,  "age_ms": 1800}
  }
}
→ {"ok": true}
```

`rssi` = the ESP32's averaged dBm, `n` = packets in the last second, `age_ms` = time since the last packet from that MAC. Only MACs heard in the last 5 s. Errors: `bad_json`, `unknown_node`.

### Register

```json
POST /api/team   {"name": "Red Rockets"}
→ {"team": "Red Rockets", "order": ["B", "C", "A"]}
```

Name trimmed, 1–24 characters, unique ignoring case. Errors: `bad_name`, `name_taken`. A phone that already has a valid cookie gets its existing team back.

### State, polled every ~1.5 s

```json
GET /api/state
→ {
  "phase": "challenge",
  "team": "Red Rockets",
  "target": "C",
  "target_name": "The Library",
  "hint": "hot",
  "trend": "steady",
  "signal": -56,
  "found": true,
  "completed": ["B"],
  "total": 3,
  "elapsed_s": 412,
  "game_status": "running",
  "challenge": {
    "type": "hold_zone",
    "goal": "Back away until you're warm, then hold still for 5 seconds",
    "status": "Too close: you're hot",
    "progress": 0.0,
    "time_left_s": 38
  }
}
```

- `phase`:
  - `join`: no valid cookie (response is just `{"phase": "join", "game_status": …}`)
  - `hunt`: current target not found yet
  - `found`: found, minigame not started (with `"codeword_required": true` if code words are on and not yet entered)
  - `challenge`: minigame running; `challenge` holds its live progress
  - `complete`: for 3 s after finishing a treasure; includes `"just_completed"` and the next target
  - `win`: all done; includes `"finish_s"` and `"place"`
- `hint`: `no_signal`, `freezing`, `cool`, `warm`, `hot`, `burning`
- `trend`: `warmer`, `colder`, `steady`
- `signal`: smoothed dBm or `null`
- `game_status`: `lobby`, `running`, `paused`, `finished`. Found detection and minigame progress only count while `running`.
- `challenge` always has `type`, `goal` (a sentence to show players), `status` (a short live line) and `progress` (0.0–1.0). `time_left_s` appears if that minigame has a time limit. A type may add fields its screen needs (for example, which step of a sequence the team is on).

### Challenges

```json
GET /api/challenge/C
→ {"type": "hold_zone", "title": "Sweet spot", "goal": "Back away until you're warm, then hold still for 5 seconds"}

POST /api/challenge/C/start
→ {"ok": true}
```

Progress and completion come through `/api/state`. There are no answers to submit. Errors: `no_team` (401), `unknown_node` (404), `not_found_yet` (403), `codeword_required` (403), `already_complete` (409), `game_not_running` (409).

### Code word (optional)

```json
POST /api/codeword/A   {"word": "Acorn "}
→ {"ok": true}   or   {"error": "bad_codeword"}
```

Trimmed and lowercased before comparing. Only required when `use_codewords` is true.

### Leaderboard

```json
GET /api/leaderboard
→ {"teams": [{"team": "Red Rockets", "completed": 3, "time_s": 1234}, …]}
```

Finished teams by `time_s`, then unfinished teams by `completed` (most first), then name. `time_s` is `null` until finished.

### Admin

```json
GET  /api/admin/status     → {"game_status", "elapsed_s", "nodes": {"A": {"name", "online", "report_age_s", "ip", "uptime_ms", "readings": {"mac": rssi}}}, "teams": [...]}
POST /api/admin/game       {"action": "start" | "pause" | "reset"}
POST /api/admin/config     {"node": "A", "found": -50, "bands": {...}, "challenge": {...}}
POST /api/admin/complete   {"team": "Red Rockets"}  → {"next": "C"}
```

Wrong or missing PIN → 401 `bad_pin`. Each team in admin status includes its current hint, signal and minigame status.

---

## config.json

```json
{
  "admin_pin": "4321",
  "poll_interval_s": 1.5,
  "stale_report_s": 3,
  "stale_mac_s": 5,
  "found_hold_s": 3,
  "complete_show_s": 3,
  "captive_mode": "online",
  "game_url": "http://10.42.0.1/",
  "treasure_macs": ["24:6f:28:aa:aa:aa", "24:6f:28:bb:bb:bb", "24:6f:28:cc:cc:cc"],
  "use_codewords": false,
  "nodes": {
    "A": {"name": "The Garden", "found": -52,
          "bands": {"burning": -50, "hot": -58, "warm": -66, "cool": -75},
          "codeword": "acorn",
          "challenge": {"type": "tbd"}},
    "B": {"name": "The Library", "found": -52,
          "bands": {"burning": -50, "hot": -58, "warm": -66, "cool": -75},
          "codeword": "quill",
          "challenge": {"type": "tbd"}},
    "C": {"name": "The Workshop", "found": -52,
          "bands": {"burning": -50, "hot": -58, "warm": -66, "cool": -75},
          "codeword": "gear",
          "challenge": {"type": "tbd"}}
  }
}
```

- `challenge.type` picks the minigame; everything else in that object belongs to the type.
- `tbd` is a placeholder that completes after a few seconds, so the whole game can be tested before real minigames exist.
- Names are placeholders (theme: named after the hiding spots). All numbers are placeholders until the walk test.
- Live edits from `POST /api/admin/config` are saved to `overrides.json` in the state folder and applied on top of `config.json` at startup. Validate that bands are strictly descending.

---

## Server rules

### Proximity (same rules as the plan)

On each `GET /api/state`: cookie → team; request IP → MAC; that MAC's readings at the team's current target.

- **Stale:** target silent for `stale_report_s` (3 s), or hasn't heard this MAC for `stale_mac_s` (5 s) → `no_signal`.
- **Smoothing:** median of the last 5 readings for that MAC at that node. Keep ~30 s of history; drop quiet MACs.
- **Bands** (lower edges, dBm): burning ≥ −50, hot ≥ −58, warm ≥ −66, cool ≥ −75, else freezing. Per treasure, from config.
- **Trend:** compared with 5 s ago; `warmer`/`colder` only for a change of 4 dB or more.
- **Found:** smoothed RSSI ≥ node `found` for `found_hold_s` in a row, while `running`. Resets on a drop or a MAC change. Once found, stays found.

### Proximity minigames

Each minigame is a small class in `server/hunt/challenges/`, registered by `type` name. It gets the team's **smoothed signal at every treasure** on each poll, because some games use more than one treasure:

```python
class Challenge:
    """One minigame type. The server handles starting, completion and saving;
    the type only judges live readings."""

    def __init__(self, node: str, settings: dict): ...

    def describe(self) -> dict:
        """Title and goal text for GET /api/challenge/{node}."""

    def progress(self, data: dict, readings: dict[str, int | None], now: float) -> tuple[dict, bool]:
        """Called on every /api/state poll while this minigame is running.
        data:     this team's saved state for this minigame (a dict it may change)
        readings: {"A": -61, "B": -77, "C": None}  smoothed RSSI, None = no signal
        returns:  (the "challenge" dict for /api/state, done?)"""
```

- `data` is stored on the team and saved with the rest of the state, so a server restart doesn't lose progress.
- On `done`, the server completes the treasure and moves the team on.
- There are no wrong answers or lockouts. A type can have a time limit; when it runs out, the type resets its own progress and the team tries again.

**Signal is noisy, so "distance" means zones:**

- Target a **band or a window** at least 8–10 dB wide, never an exact number.
- Require a **hold time** (3–5 s) on smoothed values so a lucky spike doesn't count, and reset the hold when the team leaves the zone.
- **Calibrate per treasure** in the walk test. Near distances (0.5 m vs 2 m) separate well; far ones (8 m vs 15 m) blur together.
- Two teams at one treasure disturb each other's readings, so the different treasure orders matter even more.

### Captive portal

dnsmasq answers every hostname with `10.42.0.1`. The server answers phones' connectivity probes (`/generate_204`, `/gen_204`, `/hotspot-detect.html`, `/library/test/success.html`, `/connecttest.txt`, `/ncsi.txt`, `/redirect`, `/canonical.html`, `/success.txt`) according to `captive_mode`:

- `"online"` (default): reply as if the internet works. No popup; phones less likely to switch to mobile data. Players use the QR code.
- `"redirect"`: redirect probes to `game_url`, so phones pop up the game.

Other hostnames (not `/api/…`) redirect to `game_url`. Choose the mode by testing real iPhones and Androids.

### Netinfo

- IP → MAC: `/proc/net/arp` (skip flags `0x0` and all‑zero MACs), then `/var/lib/misc/dnsmasq.leases`. MACs lowercase.
- Connected devices for admin: parse `iw dev wlan0 station dump`; return an empty list when not on a Pi.
- **Development only:** when `DEV_MAC_OVERRIDE=1`, accept an `X-Dev-MAC` header or `?mac=` so a laptop browser can act as a simulated phone. Never set on the Pi.

---

## Minigames (open, one per treasure)

Each treasure (ESP32 A, B, C) gets its own proximity minigame, still to be chosen. Guidelines: about 1–3 minutes, fair despite signal noise, and different at each treasure.

Ideas so far (none chosen):

| Idea | How it works | Possible settings |
|---|---|---|
| **Sweet spot** | Find the one ring around the treasure, e.g. stay *warm* (not hot, not cool) | `{"type": "hold_zone", "min": -68, "max": -60, "hold_s": 5}` |
| **Retreat and return** | Walk away until *freezing*, then come back to *burning* in time | `{"type": "retreat", "far": "freezing", "near": "burning", "time_limit_s": 30}` |
| **Distance combo** | Hit zones in order, like a combination lock | `{"type": "sequence", "zones": ["hot", "cool", "burning"], "hold_each_s": 3}` |
| **Midpoint** | Stand where two treasures read about the same | `{"type": "midpoint", "other": "B", "tolerance_db": 4, "hold_s": 5}` |
| **Steady hands** | Hold a zone for a long time; any drift resets | `{"type": "hold_zone", "zone": "hot", "hold_s": 10}` |

To add a minigame:

1. Agree its `type`, settings and `challenge` fields in `/api/state` (Persons 3 and 4), and add a section here.
2. Server: a class in `server/hunt/challenges/`, plus pytest tests that feed it fake readings.
3. Frontend: the screen that shows `goal`, `status` and `progress`.
4. Simulation: teach `sim/phone.py` to act it out, so it can be tested in Docker.
5. Set that treasure's `challenge` in `config.json`; tune it after the walk test.

| Treasure | Minigame | Owner | Status |
|---|---|---|---|
| A | _TBD_ | | |
| B | _TBD_ | | |
| C | _TBD_ | | |

---

## Frontend (open)

How the pages look and are built is up to their owners. These requirements come from how the system works:

- **Keep polling `GET /api/state` every ~1.5 s while the page is open.** That polling is the traffic the treasures overhear; without it the phone goes to `no_signal` and minigames stall.
- **Draw from `/api/state`**, so a refresh or reconnect never loses progress.
- **Handle every `phase` and `game_status`.**
- **Show a reconnect message** after a couple of failed polls ("make sure you're still on TreasureHunt Wi‑Fi").
- **Offline and plain HTTP** on iPhone Safari and Android Chrome: nothing from the internet, no HTTPS‑only features (e.g. Wake Lock).
- **Readable without color**: hints need a word or icon too.
- **Remind players to hold the phone normally** during minigames; how it's held changes the signal.

Pages: the player page, `/board` (big leaderboard for a laptop/TV, from `/api/leaderboard`), and `/admin/` (node status, live readings, team progress and minigame status, start/pause/reset, threshold and minigame editor, manual complete, connected devices).

Flask serves `web/` from the same address as the API, so there's no CORS or cookie trouble and the captive portal keeps working. There is only ever one server on port 80.

---

## Development with Docker

Docker is for **development only**. It copies the Pi's **network layout** and simulates the **three treasures and several phones**, so the whole game can be played on a laptop. It can't copy the Wi‑Fi radio: hostapd, channel 6, promiscuous listening and real RSSI are tested on real hardware.

### What runs

```
10.42.0.0/24 Docker network (gateway .254, so .1 stays free for the server)

  server      10.42.0.1    Flask (debug reload), serves web/, port 80 → localhost:8080
  world       10.42.0.2    knows where every phone is; turns distance into RSSI
  treasure-a  10.42.0.11   simulated ESP32 A  (MAC 24:6f:28:aa:aa:aa)
  treasure-b  10.42.0.12   simulated ESP32 B  (MAC 24:6f:28:bb:bb:bb)
  treasure-c  10.42.0.13   simulated ESP32 C  (MAC 24:6f:28:cc:cc:cc)
  phone ×N    10.42.0.x    simulated teams
```

- **Real IP → MAC lookup.** The phones and treasures really request the server over this network, so the server's `/proc/net/arp` fills in and the real lookup code runs.
- **world.py** reads `world.yaml` (treasure positions, phone paths, path‑loss settings). Phones send it their position; treasures ask it for readings. RSSI comes from the path‑loss formula `rssi = tx − 10·n·log10(d)`, with `tx` ≈ −40 dBm at 1 m, `n` ≈ 3 indoors, plus ±5 dB noise. Tune these to match the walk test later.
- **treasure.py** posts the exact ESP32 report format every second, with `NODE_ID` from its environment.
- **phone.py** registers a team, polls `/api/state` every 1.5 s, walks toward its current target, starts the minigame when found, and acts out each minigame type it knows.
- **Your own browser** at `http://localhost:8080` arrives from Docker's gateway, not a phone container, so its MAC means nothing. With `DEV_MAC_OVERRIDE=1`, add `?mac=02:00:00:00:00:99` to play as a manual phone. A nice‑to‑have is a small map page on `world` where you drag that phone around.

### Compose file (sketch)

```yaml
networks:
  hunt:
    ipam:
      config:
        - subnet: 10.42.0.0/24
          gateway: 10.42.0.254

x-sim: &sim
  build: ./sim
  volumes: ["./sim:/sim"]
  depends_on: [server, world]

services:
  server:
    build: ./server
    volumes: ["./server:/app", "./web:/web"]
    environment: [FLASK_DEBUG=1, DEV_MAC_OVERRIDE=1, WEB_DIR=/web, HUNT_STATE=/app/state.json]
    command: flask --app app run --host 0.0.0.0 --port 80
    ports: ["8080:80"]
    networks: {hunt: {ipv4_address: 10.42.0.1}}

  world:
    <<: *sim
    command: python world.py
    depends_on: []
    networks: {hunt: {ipv4_address: 10.42.0.2}}

  treasure-a: {<<: *sim, command: python treasure.py, environment: [NODE_ID=A], mac_address: "24:6f:28:aa:aa:aa", networks: {hunt: {ipv4_address: 10.42.0.11}}}
  treasure-b: {<<: *sim, command: python treasure.py, environment: [NODE_ID=B], mac_address: "24:6f:28:bb:bb:bb", networks: {hunt: {ipv4_address: 10.42.0.12}}}
  treasure-c: {<<: *sim, command: python treasure.py, environment: [NODE_ID=C], mac_address: "24:6f:28:cc:cc:cc", networks: {hunt: {ipv4_address: 10.42.0.13}}}

  phone:
    <<: *sim
    command: python phone.py
    networks: [hunt]
```

### Commands

```bash
docker compose up --build                  # server, world, 3 treasures, 1 phone
docker compose up --scale phone=6          # six simulated teams
docker compose logs -f server
docker compose exec server pytest          # server tests
docker compose down -v                     # stop and clear state
```

Then open `http://localhost:8080/admin/` to watch the simulated teams, or `http://localhost:8080/?mac=02:00:00:00:00:99` to play.

The server and web folders are mounted, so edits show up on refresh (Flask reloads Python changes automatically).

### Without Docker

Anyone can still use a virtual environment: `python3 -m venv .venv`, `pip install -r server/requirements.txt`, `flask --app app run --port 8080` from `server/` with `DEV_MAC_OVERRIDE=1`, and run the `sim/` scripts pointed at `localhost`. IP → MAC lookup isn't meaningful this way, which is what the dev override is for.

**Match the Pi's Python version** (`python3 --version` on the Pi) in both Dockerfiles, and keep versions pinned in `requirements.txt`.

---

## Production on the Pi

No Docker on the Pi. Production is the Pi on game day: it has to start reliably after a power cut, recover from crashes, and be fixable in minutes with no internet.

- **Code** is a git clone at `/opt/treasurehunt`, with a virtual environment at `/opt/treasurehunt/.venv` built from `server/requirements.txt` during setup (over Ethernet, which has internet).
- **State** lives at `/var/lib/treasurehunt/` (`state.json`, `overrides.json`).
- **Service** (`treasurehunt-server.service`, update from the Go version):

```ini
[Service]
User=hunt
WorkingDirectory=/opt/treasurehunt/server
Environment=HUNT_STATE=/var/lib/treasurehunt/state.json WEB_DIR=/opt/treasurehunt/web
ExecStart=/opt/treasurehunt/.venv/bin/waitress-serve --listen=0.0.0.0:80 --threads=8 --call app:create_app
AmbientCapabilities=CAP_NET_BIND_SERVICE
StateDirectory=treasurehunt
Restart=always
RestartSec=2
```

- **Deploy:** `ssh <user>@huntbase.local`, then `cd /opt/treasurehunt && git pull && sudo systemctl restart treasurehunt-server`. Logs: `journalctl -u treasurehunt-server -f`. On game day, SSH in from a laptop joined to TreasureHunt at `10.42.0.1`.
- **Network setup:** `cd pi-setup && sudo ./setup.sh` over Ethernet (never over Wi‑Fi; it takes `wlan0`). Optionally `sudo COUNTRY=CA ./setup.sh`. It should also create the venv and install the server service.
- **Backup:** once the Pi is fully working and calibrated, copy the SD card to an image and flash it to a **spare card**. If the card dies on game day, swap it.
- **Power:** check `vcgencmd get_throttled` shows `0x0`. Keep the Pi on wall power if possible.

dnsmasq hands out `10.42.0.20–200`. Treasures can get fixed `10.42.0.11–13` with the commented `dhcp-host=` lines in `dnsmasq-treasurehunt.conf` (the same addresses the Docker simulation uses).

---

## ESP32 sketch (`esp32-node/`)

Same sketch on all three boards; only `NODE_ID` changes.

```cpp
const char* NODE_ID    = "A";                      // "A", "B" or "C"
const char* WIFI_SSID  = "TreasureHunt";            // open network: WiFi.begin(WIFI_SSID)
const char* REPORT_URL = "http://10.42.0.1/api/report";
```

1. `WiFi.mode(WIFI_STA)`, `WiFi.begin(WIFI_SSID)`, retry until joined (this sets the radio to channel 6).
2. `esp_wifi_set_promiscuous_rx_cb`, filter data + management frames, `esp_wifi_set_promiscuous(true)`.
3. Callback (tiny: no printing, no networking): read `rx_ctrl.rssi` and the sender MAC (address 2); keep only frames sent to the Pi's access point; skip own MAC and the Pi's; update the entry under a `portMUX` lock.
4. Per‑MAC average `avg = 0.7·avg + 0.3·new`, packet count, last‑heard time. Table capped at ~32; drop MACs quiet for 10 s.
5. Every 1 s: copy the table and POST the report JSON (MACs heard in the last 5 s).
6. Reconnect if disconnected; `ESP.restart()` after 30 s with no successful report. LED on GPIO 2: solid = reporting, blinking = connecting. Serial at 115200 with a `WATCH_MAC` option for the walk test. Print own MAC at boot for `treasure_macs`.

---

## Team roles and jobs

Four owners, split by layer. Write each person's name next to their role.

| Role | Owns | Busiest in | Works most with |
|---|---|---|---|
| **1. Base station and network** — _name:_ | `pi-setup/`, `server/hunt/netinfo.py`, `web/admin/`, game‑day logistics | Weeks 1 and 4 | Person 2 (radio), Person 3 (server on the Pi) |
| **2. Treasures and simulation** — _name:_ | `esp32-node/`, `sim/`, `docker-compose.yml`, power, enclosures, calibration | Weeks 1–3 | Person 1 (network), Person 3 (reports) |
| **3. Game server** — _name:_ | `server/` (except `netinfo.py`), minigame logic, tests | Weeks 1–3 | Person 4 (API and minigames) |
| **4. Player experience and minigame design** — _name:_ | `web/` player page and `/board`, minigame design, rules sheet, playtesting | Weeks 1–4 | Person 3 (API) |

### 1. Base station and network

- [x] Flash Raspberry Pi OS Lite (64‑bit), hostname `huntbase`, SSH on
- [x] hostapd + dnsmasq configs, IP service and `setup.sh`; network broadcasts
- [ ] Make the network visible on **iPhone** (try commenting out `ieee80211d`/`ieee80211n`), then check Android
- [ ] Confirm network, DHCP and wildcard DNS come back on their own after `sudo reboot`
- [ ] Update `setup.sh` and `treasurehunt-server.service` for Flask: clone to `/opt/treasurehunt`, create the venv, install and enable the service
- [ ] `netinfo.py`: IP → MAC (ARP, then leases), connected devices from `iw`, dev MAC override
- [ ] Test captive behavior (`online` vs `redirect`) on iPhone and Android; record the choice here
- [ ] Admin page in `web/admin/`
- [ ] Capacity test: 3 treasures + 7 phones, every phone gets hints, Pi CPU under ~50% in `top`
- [ ] Decide open vs WPA2 and the overlay filesystem for game day
- [ ] Make the SD card backup image and spare card
- [ ] Print QR signs; own the game‑day checklist

### 2. Treasures and simulation

- [ ] **First:** Docker simulation (`world.py`, `treasure.py`, a basic `phone.py`, `docker-compose.yml`), since Persons 3 and 4 depend on it
- [ ] Arduino IDE with the ESP32 board package
- [ ] Sketch: join the open network, auto‑reconnect, restart after 30 s without a successful report, LED status
- [ ] Sketch: promiscuous listening, per‑MAC averaging, filter to frames sent to the Pi, skip own/Pi MAC
- [ ] Sketch: JSON report to `/api/report` every second
- [ ] Record each ESP32's MAC in `treasure_macs` and the `dhcp-host=` lines
- [ ] Bench test with Person 1: one ESP32, one phone, readings on the admin page
- [ ] Power banks: auto‑shutoff test and 2‑hour soak; plastic enclosures
- [ ] Lead the walk test; set thresholds in `config.json`; tune the simulation's path‑loss settings to match
- [ ] Teach `phone.py` each minigame type as it's added
- [ ] Choose hiding spots with Person 4

### 3. Game server

- [ ] `app.py` skeleton: `create_app()`, cookies, serving `WEB_DIR`, captive probes, error format
- [ ] `hunt/state.py`: game, teams, node readings, one lock, atomic save and load
- [ ] `/api/report` and `hunt/proximity.py`: stale checks, median, bands, trend, found rule (port from the Go skeleton)
- [ ] Team registration, round‑robin orders, progression, `complete` and `win` phases, leaderboard
- [ ] Minigame framework: `Challenge` base class, registry, start endpoint, per‑team `data`, `tbd` type
- [ ] Code words (optional feature)
- [ ] Admin endpoints with PIN, including live config and `overrides.json`
- [ ] `requirements.txt` (pinned) and the server `Dockerfile`
- [ ] pytest: proximity, found timing, progression, each minigame type with fake readings, restart keeps state
- [ ] Build each minigame type as the team designs them

### 4. Player experience and minigame design

- [ ] Choose the frontend approach; build the player page against the contracts (use the Docker simulation)
- [ ] Hot/cold display, trend, progress, reconnect message
- [ ] Minigame screen(s) showing `goal`, `status`, `progress` and time left
- [ ] Lead minigame design for A, B and C with the team; write each one's section in this README
- [ ] `/board` leaderboard page
- [ ] Test on iPhone Safari and Android Chrome
- [ ] Player rules sheet: keep the page open and screen on, stay connected / turn off mobile data, hold the phone normally, "not secure" warning is fine
- [ ] Choose hiding spots and treasure names with Person 2
- [ ] Run the full playtest with outside players; time each minigame; collect feedback

### Who depends on whom

- **Critical path:** Person 1's network and Person 2's ESP32 report must work by the end of week 1. Everything real depends on them.
- **Person 2's Docker simulation unblocks Persons 3 and 4.** Until it exists, fake a report by hand: `curl -X POST localhost:8080/api/report -H 'Content-Type: application/json' -d '{"node":"A","uptime_ms":1,"readings":{"02:00:00:00:00:99":{"rssi":-60,"n":4,"age_ms":100}}}'`
- **Minigames touch three people:** Person 4 designs the game and screen, Person 3 writes the server logic, Person 2 teaches the simulated phone to play it. Agree the settings and `challenge` fields before building.
- The admin page (Person 1) uses admin endpoints built by Person 3.

---

## Working rules

- One shared GitHub repo. Work on your own branch, open a pull request, one other person reviews it.
- Stay in your own folders and files (see the roles table).
- Changes to the **interface contracts**, `config.json` shape, or network settings (SSID, channel, open/WPA2, IP) need a heads‑up in the group chat first.
- Develop against the Docker simulation so nobody is blocked on the one Pi.
- Deploy with `git pull` on the Pi and `sudo systemctl restart treasurehunt-server`.
- Add anything that affects the others to the changelog below.

---

## Timeline

| When | Milestone | Done when |
|---|---|---|
| Day 1 | Kickoff | Contracts agreed, repo created, hardware ordered, names filled in |
| End of week 1 | Pieces work alone | Network works on iPhone and Android; one ESP32 prints phone readings; Docker simulation runs; server passes tests against it; player page shows hints from simulated data |
| End of week 2 | First integration | Real ESP32 reports reach the Pi; a phone sees live hints for one treasure; first minigame works in the simulation |
| Middle of week 3 | Full game on hardware | All 3 treasures and minigames, win screen and leaderboard work end to end |
| End of week 3 | Calibrated | Walk test done; thresholds and minigame zones in `config.json`; battery soak passed; SD card backed up |
| Week 4 | Playtest and polish | One full playtest with outside players; fixes made; rules and QR signs printed |

Software integration check: `docker compose up --scale phone=6` plays full games to the win screen, and a browser with `?mac=` can play one by hand, with results on `/board` and `/admin/`.

---

## Game‑day checklist

**Night before:** charge every power bank plus spares; `git pull` on the Pi and confirm calibrated `config.json`; print QR signs, rules sheets; pack cables, admin laptop, Pi wall charger, spare SD card.

**Setup (30 min before):** place the Pi centrally on wall power; power on, wait ~60 s, join TreasureHunt from the admin laptop; hide and power the treasures, check LEDs are solid; admin page shows all three online with report age under 3 s; walk once with a phone past each treasure and try each minigame; reset the game; post the QR signs.

**During:** watch the admin page for treasures going offline; help "no signal" teams (still on TreasureHunt, mobile data off, page open, screen on); manual complete only for real technical failures.

**After:** final leaderboard on `/board`; `sudo shutdown now` before unplugging the Pi; collect everything; note what to improve.

---

## Open decisions

| Decision | Options | Current default |
|---|---|---|
| Minigame at each treasure | See **Minigames** | Open |
| Frontend approach | Plain HTML/JS, or a framework with a build step | Open (Person 4) |
| Teams | ~7 phones on built‑in Wi‑Fi; more needs a USB adapter | Up to 6 teams, one phone each |
| Time limit for the whole game | None or fixed | 30–45 min |
| Code words | Proximity only, or also a code word at each treasure | Off (the minigames already prove presence) |
| Captive mode | `online` or `redirect` | `online`, pending phone tests |
| Open vs WPA2 | Open (strangers can use a slot) or WPA2 (password on the QR sign) | Open |
| Overlay filesystem | On (safe SD card, state lost on reboot) or off | Off, Pi on wall power |
| iPhone visibility fix | Drop 802.11n/d in `hostapd.conf` | Being tested |

---

## Changelog

- **Sep 23:** Project plan written.
- **Sep 26:** Network switched from NetworkManager to hostapd + dnsmasq, made open (no password). Go server tried and dropped: staying with Flask since only one team member knows Go. Game logic split from Flask routes; frontend moved to its own `web/` folder, approach open. Minigames changed to proximity challenges (reach and hold a distance zone), one per treasure, still to be chosen. Docker Compose added for development only: simulated Pi network, three treasures and several phones. Production stays plain Pi with systemd, plus an SD card backup.

