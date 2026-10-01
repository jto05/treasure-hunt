# Wi-Fi Treasure Hunt

A 3-treasure scavenger hunt over Wi-Fi. Phones get live hot/cold proximity
hints; at each treasure the team plays a proximity minigame (reach and hold
the right distance) to complete it.

- **Raspberry Pi 3 B+** — base station: runs the Wi-Fi network and the
  Flask game server (all game logic).
- **Three ESP32 boards** — the hidden treasures. They overhear phones'
  Wi-Fi packets, average signal strength (RSSI) per MAC, and POST it to
  the Pi every second.
- **Phones** — display only, one per team, served a web page by the Pi.

Everything below is the shared contract the four of you build against.
Everything not covered here (frontend design, minigame choice, exact
thresholds, network security, deployment details, etc.) is open — agree
on it as a team as you go.

## API endpoints

All JSON. Errors are a 4xx status with `{"error": "<code>"}`.

| Method & path | Called by | Purpose |
|---|---|---|
| `POST /api/report` | ESP32 / simulated treasure | Signal readings from one treasure, once per second |
| `POST /api/team` | Player page | Register a team; sets a session cookie |
| `GET /api/state` | Player page | Everything the page needs to draw itself (hint, progress, phase) |
| `GET /api/challenge/{node}` | Player page | Description of that treasure's minigame |
| `POST /api/challenge/{node}/start` | Player page | Start the minigame |
| `GET /api/leaderboard` | Player page, board display | Rankings |
| `GET /api/admin/status` | Admin page | Node status, live readings, teams |
| `POST /api/admin/game` | Admin page | Start / pause / reset the game |

Example:

```json
POST /api/report
{"node": "B", "readings": {"a4:5e:60:12:34:56": {"rssi": -58, "n": 14, "age_ms": 200}}}
→ {"ok": true, "watch_macs": ["a4:5e:60:12:34:56"]}

POST /api/team {"name": "Red Rockets"}
→ {"team": "Red Rockets", "order": ["B", "C", "A"]}

GET /api/state
→ {"phase": "hunt", "target": "C", "hint": "warm", "signal": -66, "found": false}
```

**How a registered phone's MAC reaches the ESP32:** there's no direct
link between them — it's routed through the server via two endpoints.
`POST /api/team` looks up the registering phone's MAC from its request IP
and stores it against that team. Every `POST /api/report` response then
echoes back `watch_macs`, the full list of MACs across all registered
teams, so each treasure knows which signals are actually worth reporting
next time instead of every phone it overhears.

Exact field names, extra endpoints (code words, live config editing,
captive portal probes, etc.) and full response shapes are open — agree on
them as you build each side.

## Distance calculation

Treasures don't measure distance directly — they measure Wi-Fi signal
strength (RSSI, in dBm) from each phone, and the server turns that into a
hot/cold hint:

1. **Report:** each ESP32 overhears phone packets, averages RSSI per phone
   MAC address, and POSTs it to the server every second.
2. **Smoothing:** the server takes the median of the last few readings per
   phone/treasure pair, so one noisy packet doesn't cause a false hint.
3. **Bands:** the smoothed RSSI is mapped to a hot/cold zone (e.g. burning
   / hot / warm / cool / freezing) using dBm thresholds — closer to the
   treasure means a stronger (less negative) RSSI.
4. **Found rule:** a treasure counts as "found" once the smoothed signal
   stays at or above a threshold for a few seconds in a row (a hold time),
   so a brief spike doesn't count.

Exact thresholds, band count, hold times, and trend logic are open — they
need to be calibrated per treasure with a real walk test, since
RSSI-to-distance varies by environment.

## Tools needed

- **Raspberry Pi 3 B+** — runs the Wi-Fi access point and the game server.
- **Three ESP32 boards** — the hidden treasures, running Arduino/ESP-IDF
  firmware to listen for Wi-Fi packets and report RSSI.
- **Python 3 / Flask / waitress** — the game server (all endpoints and
  game logic).
- **hostapd + dnsmasq** — turns the Pi into an open Wi-Fi access point
  with DHCP/DNS.
- **Any phone with a browser** — no app, just a web page served by the
  Pi.

Everything else — frontend framework/approach, minigame design, network
security, deployment setup, simulation/testing tooling — is open for the
team to decide.

---

For the full original design spec, decisions log, team roles, timeline
and other project detail, see [`readme_v2.md`](./readme_v2.md).
