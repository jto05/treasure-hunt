#!/usr/bin/env python3
"""
Parse ESP32 serial-monitor captures (the "mac rssi=X n=Y" lines printed by
report.cpp) into a CSV, for tuning this sim's noise model against real
hardware readings.

Capture logs like:
    cd esp32-node/node_A
    make monitor | tee ~/captures/dist_3m.log

Each log's filename should say what distance it was captured at, e.g.
"dist_3m.log" or "3m_wall.log" -- a number immediately followed by "m".
If a filename doesn't fit that pattern, pass --distance to label it
explicitly instead of renaming it.

Usage:
    python3 parse_captures.py dist_1m.log dist_3m.log dist_5m.log
    python3 parse_captures.py weird_name.log --distance weird_name.log=7.5
"""
import argparse
import csv
import re
import sys
from pathlib import Path

LINE_RE = re.compile(
    r"^\s*(?P<mac>[0-9a-f]{2}(?::[0-9a-f]{2}){5})\s+rssi=(?P<rssi>-?\d+)\s+n=(?P<n>\d+)",
    re.IGNORECASE,
)
DIST_RE = re.compile(r"(\d+(?:\.\d+)?)\s*m\b", re.IGNORECASE)


def infer_distance(path, overrides):
    if path.name in overrides:
        return overrides[path.name]
    m = DIST_RE.search(path.stem)
    if not m:
        raise ValueError(
            f"can't infer distance from filename {path.name!r} -- "
            f"rename it to include e.g. '_3m', or pass "
            f"--distance {path.name}=<meters>"
        )
    return float(m.group(1))


def parse_file(path, distance):
    rows = []
    with path.open() as f:
        for seq, line in enumerate(f):
            m = LINE_RE.match(line)
            if not m:
                continue
            rows.append({
                "distance_m": distance,
                "seq": seq,
                "mac": m["mac"].lower(),
                "rssi": int(m["rssi"]),
                "n": int(m["n"]),
                "source_file": path.name,
            })
    return rows


def parse_override(spec):
    name, _, value = spec.partition("=")
    if not value:
        raise argparse.ArgumentTypeError(f"expected FILE=DISTANCE, got {spec!r}")
    try:
        return name, float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"distance must be a number, got {value!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="+", type=Path,
                     help="serial capture log file(s), e.g. dist_3m.log")
    ap.add_argument("-o", "--output", type=Path, default=Path("captures.csv"),
                     help="output CSV path (default: captures.csv)")
    ap.add_argument("--distance", action="append", default=[], type=parse_override,
                     metavar="FILE=DISTANCE",
                     help="override/define distance (meters) for a file whose "
                          "name doesn't match '<number>m' (repeatable)")
    args = ap.parse_args()

    overrides = dict(args.distance)
    all_rows = []
    for path in args.logs:
        try:
            distance = infer_distance(path, overrides)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

        rows = parse_file(path, distance)
        if not rows:
            print(f"warning: no rssi/n lines matched in {path}", file=sys.stderr)
        print(f"{path.name}: distance={distance}m, {len(rows)} readings")
        all_rows.extend(rows)

    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["distance_m", "seq", "mac", "rssi", "n", "source_file"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"wrote {len(all_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
