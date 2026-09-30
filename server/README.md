# server/

Person 3's folder (game server), except `hunt/netinfo.py` (Person 1). Flask
app + game logic. Pinned dependencies here are the single list used by the
Pi, laptops and Docker alike.

**Hard rule: `hunt/` has no Flask imports.** Every module in there takes
plain Python values and returns results, so it's unit-testable without a
request context. `app.py` is the only place that touches Flask — it parses
requests, calls into `hunt`, and returns JSON.

See the top-level `README.md` for the full API contracts, `config.json`
shape, and game rules this folder has to satisfy. This file is just a map
of what's expected in each empty file here.

## Layout

```
server/
  app.py                  create_app(): routes, cookies, admin PIN, captive probes, serves web/
  hunt/                   game logic, no Flask imports
    config.py             load config.json + overrides.json, merge, validate
    state.py               Game, Team, node reading history, one lock, atomic save/load
    proximity.py            smoothing, bands, trend, found rule
    progression.py          round-robin orders, completion, win, leaderboard
    netinfo.py               IP -> MAC, connected devices (Person 1)
    challenges/               proximity minigame types, one file per type
      __init__.py             registry: type name -> class
      base.py                  Challenge base class
      tbd.py                   placeholder type used until real minigames exist
  tests/                    pytest, one file per hunt/ module
  config.json               thresholds, treasure MACs, challenge settings, admin PIN
  requirements.txt          pinned; used by the Pi, laptops and Docker alike
  Dockerfile                development image
```

## `app.py`

`create_app(config_path=None, now=...)` factory. Owns:

- Loading `config.json` (+ `overrides.json`) via `hunt.config`, and one
  `hunt.state.GameStore` (the lock + persisted state).
- All routes from the interface contract table in the top-level README:
  `/api/report`, `/api/team`, `/api/state`, `/api/challenge/{node}`,
  `/api/challenge/{node}/start`, `/api/codeword/{node}`,
  `/api/leaderboard`, `/api/admin/*`.
- The team cookie: `team`, random token, `HttpOnly`, `SameSite=Lax`, 24 h.
- Admin PIN check: `X-Admin-Pin` header, wrong/missing -> 401 `bad_pin`.
- Captive-portal probe paths (`/generate_204`, `/hotspot-detect.html`,
  etc.) answered per `config["captive_mode"]`.
- Serving `web/` (`WEB_DIR` env var) from the same address as the API —
  no CORS, one server on port 80.
- An injectable `now()` so tests control time; the Pi has no reliable
  clock, so game time is always elapsed-since-start, never wall time.

Every handler should be thin: pull cookie/IP/body, call one or two
`hunt.*` functions, translate the result into the JSON shapes documented
in the top-level README, map domain errors to the listed error codes.

## `hunt/config.py`

- `load_config(path=None) -> dict`: read `config.json`, then merge
  `overrides.json` on top if it exists (deep merge, overrides win).
- `validate_config(config)`: enforce invariants — e.g. each node's
  `bands` must be strictly descending (burning > hot > warm > cool).
- `save_overrides(path, overrides)`: merge into `overrides.json` and
  atomic-write it (temp file + `os.replace`), for `POST /api/admin/config`.

## `hunt/state.py`

- `Team`: name, token, treasure `order`, `completed` list, `start_s`,
  `finish_s`, per-node found/challenge/codeword state. Needs `to_dict` /
  `from_dict` so it round-trips through `state.json`.
- `Game`: `status` (`lobby`/`running`/`paused`/`finished`), `start_s`,
  round-robin cursor, `teams` keyed by cookie token.
- `GameStore`: the **one lock** guarding all game state (Waitress serves
  on several threads), plus per-node signal history. `save()` writes
  `state.json` atomically (temp file, flush, `os.replace`) on every
  change. Signal readings themselves are not persisted — only team/game
  progress — since they're live sensor data, not something a restart
  needs to remember.
- `known_macs()`: every registered team's phone MAC (set via
  `register_team`, looked up through `hunt.netinfo.ip_to_mac` at
  `POST /api/team` time). Echoed back as `watch_macs` in every
  `POST /api/report` response, so each treasure knows which MACs are
  actually worth reporting instead of everything it overhears.

## `hunt/proximity.py`

Per the top-level README's **Server rules > Proximity** section:

- Stale check: target silent for `stale_report_s`, or this MAC not heard
  for `stale_mac_s` -> no signal.
- Smoothing: median of the last 5 readings for a MAC at a node.
- Bands from config, lower edges: burning / hot / warm / cool / else
  freezing.
- Trend: compare against ~5 s ago; `warmer`/`colder` only for a 4 dB+
  change, else `steady`.
- Found rule: smoothed RSSI at/above the node's `found` threshold for
  `found_hold_s` in a row while the game is `running`. A drop resets the
  hold timer. Once found, stays found.

Takes plain values (MAC, rssi, timestamps) — no knowledge of teams,
Flask, or config file structure.

## `hunt/progression.py`

- Round-robin through the 6 permutations of `A`/`B`/`C` so teams spread
  out at registration.
- Current target, marking a treasure complete, detecting the win
  condition (sets `finish_s`).
- Leaderboard ordering: finished teams by `time_s`, then unfinished by
  treasures completed (most first), then name.

## `hunt/netinfo.py` (Person 1)

- IP -> MAC: `/proc/net/arp` first (skip flags `0x0` and all-zero MACs),
  then `/var/lib/misc/dnsmasq.leases`. Lowercase MACs.
- Connected devices for the admin page: parse
  `iw dev wlan0 station dump`; return `[]` when not on a Pi.
- Dev override: when `DEV_MAC_OVERRIDE=1`, accept an `X-Dev-MAC` header
  or `?mac=` query param so a laptop browser can act as a phone. Never
  set this on the Pi.

## `hunt/challenges/`

- `base.Challenge`: `__init__(node, settings)`, `describe() -> dict`
  (title/goal for `GET /api/challenge/{node}`), and
  `progress(data, readings, now) -> (challenge_dict, done)` called on
  every poll while the minigame is running. `readings` is smoothed RSSI
  per node (`None` = no signal), since some minigame types (midpoint,
  sequence) need more than one treasure's signal.
- `__init__.py`: `REGISTRY` mapping a `type` string to its class, plus
  `make_challenge(node, settings)`. New minigames get one file here and
  one line in the registry.
- `tbd.py`: the placeholder type — completes on its own after a short
  delay, so the full game (registration -> hunt -> found -> challenge ->
  win) can be exercised before any real minigame exists. Every treasure's
  `challenge.type` in `config.json` should start as `"tbd"`.

Real minigame types (see the top-level README's **Minigames** table —
`hold_zone`, `retreat`, `sequence`, `midpoint`, or whatever gets chosen)
each get their own file here once designed with Person 4.

## `tests/`

One file per `hunt/` module, fed fake readings/timestamps — no Flask test
client needed for these. Cover at minimum:

- `proximity`: staleness, smoothing, bands, trend, the found rule
  (including hold-time and reset-on-drop).
- `progression`: round-robin order assignment, completion, win, and
  leaderboard ordering.
- `state`: atomic save + reload keeps a team's progress (a restart must
  not lose state).
- `challenges`: each type's `progress()` against scripted readings,
  including the `tbd` placeholder.

`conftest.py` just needs `server/` on `sys.path` so `import hunt` works
regardless of the pytest invocation directory.

## `config.json`

Shape is fixed by the top-level README's **config.json** section:
`admin_pin`, timing knobs (`poll_interval_s`, `stale_report_s`,
`stale_mac_s`, `found_hold_s`, `complete_show_s`), `captive_mode`,
`game_url`, `treasure_macs`, `use_codewords`, and `nodes.{A,B,C}` (name,
`found` threshold, `bands`, `codeword`, `challenge`). Live edits via
`POST /api/admin/config` land in `overrides.json`, not this file.

## `requirements.txt` / `Dockerfile`

`requirements.txt` is pinned and shared by the Pi, laptops and Docker —
don't add a dependency here without updating all three. Match the Pi's
Python version (`python3 --version` on the Pi) in `Dockerfile`.
