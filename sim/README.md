# sim/

Lets the team develop against a live game server without real ESP32
hardware. `treasure.py` plays the part of the treasure nodes, posting
`/api/report` calls the same way the real firmware does, so the
frontend (or anyone testing `/admin`, `/register`) always has live,
moving data to look at.

## Quick start

```
cd server && make run          # the game server, in one terminal
cd sim && make run             # the simulator, in another
```
Open `http://localhost:8080/admin` and watch readings for
`aa:aa:aa:aa:aa:01` update every second across nodes A, B, C.

## `treasure.py` — the simulator

Nodes are placed along a single line, evenly spaced, named A, B, C...
in order. One simulated phone moves along that same line; its distance
to every node falls out of its single position, so moving closer to
one node is automatically moving farther from whichever is behind it —
no per-node bookkeeping needed.

Run it directly, or through the Makefile (see below):
```
python3 treasure.py
python3 treasure.py --num-nodes 5 --node-spacing 15 --behavior approach
python3 treasure.py --mac aa:aa:aa:aa:aa:02 --behavior retreat --speed 2
```

| flag | default | meaning |
|---|---|---|
| `--server` | `http://localhost:8080` | game server base URL |
| `--num-nodes` | `3` | how many nodes to simulate, named A, B, C... |
| `--node-spacing` | `10` | meters between adjacent nodes |
| `--behavior` | `wander` | `approach` (walk toward the far node), `retreat` (walk toward the near node), or `wander` (jitter in place) |
| `--speed` | `1.0` | walking speed in m/s, only matters for approach/retreat |
| `--mac` | `aa:aa:aa:aa:aa:01` | the fake phone MAC to report |
| `--interval` | `1.0` | seconds between report rounds |

`approach`/`retreat` bounce off the ends of the line instead of
stopping, so a run keeps producing changing data indefinitely.

**Multiple phones at once**: run multiple instances against the same
server with different `--mac` (and optionally different `--behavior`)
— e.g. one approaching while another retreats. The server tracks each
MAC independently, so this just works.

**Why it skips real team registration**: on a dev machine there's no
dnsmasq, so a real `/api/team` registration always resolves to
`mac=None`, and the server would never tell a real treasure node to
track it (`watch_macs` would always come back empty). `treasure.py`
reports its fake MAC unconditionally instead, which is what's actually
useful for feeding a frontend dev live data.

**Where the RSSI numbers come from**: a path-loss curve fit to real
hardware captures (see `CAPTURES.md`), not made up:
```
rssi(d) ~= -51.4 - 24.5*log10(d) + gauss(0, 3.7)
```
Fit from only 3 distances (1m/4m/10m), so it's an approximation —
good enough to look real, not a precise model. More captures tighten
the fit; see `CAPTURES.md` for how to add them.

## `parse_captures.py` — turning real captures into data

Parses the `mac rssi=X n=Y` lines the real firmware already prints
over serial into a CSV (`distance_m,seq,mac,rssi,n,source_file`), used
to fit the numbers `treasure.py` uses above. See `CAPTURES.md` for the
full capture procedure (what to record, at what distances, how to name
the files).

## Makefile targets

```
make help      # list targets and current variable values
make run       # run the simulator (SERVER, NUM_NODES, SPACING, BEHAVIOR, SPEED, MAC, INTERVAL)
make parse     # parse capture logs into a CSV (LOGS=glob, required; OUT=path)
make clean     # remove the generated CSV and __pycache__
```
Override any variable on the command line, e.g.
`make run BEHAVIOR=approach NUM_NODES=5`.
