# Capturing real RSSI data for the simulator

Before writing the treasure-node simulator (`treasure.py`/`phone.py`/
`world.py`), we need real labeled data to fit its noise model against,
instead of guessing at RSSI/noise numbers. This records how that data
is being collected, so it's reproducible and anyone on the team can
add more captures the same way.

## What we're capturing

For a phone at a **known, fixed distance** from a real treasure board,
`report.cpp` already prints one line per report cycle:
```
a6:cd:24:c8:9b:d6 rssi=-51 n=4
```
`rssi` is the raw (pre-smoothing) signal strength, `n` is packets heard
that cycle. Capturing this at several known distances gives us
`(distance, rssi, n)` samples to characterize how RSSI falls off with
distance and how noisy it is at each range.

## Step by step

1. **Flash a board** with the current firmware (`cd esp32-node/node_A
   && make flash` or whichever board has hardware attached).

2. **Pick distances to sample.** So far: 1m, 3m, 5m, 10m, and one
   "behind a wall" non-line-of-sight case. Add more if a gap in the
   curve looks important once we see the data.

3. **For each distance:**
   - Place the phone at that distance from the board, screen on,
     browser open to `/register` (so it's actually generating Wi-Fi
     traffic via the keep-alive `fetch` loop, not just sitting idle).
   - Capture the serial output for about 60 seconds:
     ```
     cd esp32-node/node_A
     make monitor | tee ~/captures/dist_<N>m.log
     ```
     Ctrl+C to stop after ~60s. The filename must contain `<number>m`
     (e.g. `dist_3m.log`) so `parse_captures.py` can infer the distance
     automatically — if a capture can't be named that way, its distance
     can be supplied explicitly at parse time instead (see below).

4. **Repeat per distance**, and per board if we suspect boards differ
   physically (e.g. antenna orientation, enclosure).

## Turning captures into data

Once a batch of `.log` files exists:
```
cd sim
python3 parse_captures.py ~/captures/dist_*.log -o captures.csv
```
This produces one CSV (`distance_m,seq,mac,rssi,n,source_file`)
covering every capture, skipping all the non-reading lines (connection
messages, `sent=ok` lines, etc). Pass `--distance FILE=METERS` for any
capture whose filename doesn't fit the `<number>m` pattern.

## Captures collected so far

| file | distance | board | notes |
|---|---|---|---|
| _(none committed yet)_ | | | |

Update this table each time a new capture is added, so it's clear
what's already covered and what distances are still missing.

## Next step

Once there's enough spread across distances, fit a simple model from
`captures.csv` (mean RSSI vs. distance -> path-loss curve, spread at
each distance -> noise term, distribution of `n` -> activity level)
and use that to drive `treasure.py`'s fake readings instead of
hand-picked numbers.
