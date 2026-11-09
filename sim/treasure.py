#!/usr/bin/env python3
"""
Simulates the treasure nodes' calls to the game server (POST /api/report)
so the frontend can be developed against live, flowing data without real
ESP32 hardware.

RSSI is generated from a path-loss curve fit to real captures (see
CAPTURES.md / captures.csv):
    rssi(d) ~= RSSI_AT_1M - 10*PATH_LOSS_EXPONENT*log10(d) + gauss(0, NOISE_STD_DB)
Fit from only 3 distances (1m/4m/10m) so it's an approximation, off by a
few dB at 4m specifically -- good enough to look real, not a precise model.

Nodes are placed along a line, evenly spaced (--node-spacing), named
A, B, C... in order. A single simulated phone moves along that same
line -- --behavior picks whether it walks toward the far node
(approach), the near node (retreat), or just jitters in place (wander,
the default), bouncing back and forth at the ends so it never stops
moving. Distance to each node is just abs(phone_pos - node_pos), so
with multiple nodes, approaching one is automatically receding from
whichever one is behind it -- no separate per-node bookkeeping needed.

To simulate several phones with different behaviors at once, run
multiple instances against the same server with different --mac and
--behavior values.

Deliberately skips team registration and the watch_macs reply real
firmware respects -- on a dev machine with no dnsmasq, a registered
team's mac always resolves to None, so watch_macs would always come
back empty and nothing would ever get reported. This reports its fake
mac unconditionally instead.

Usage:
    python3 treasure.py
    python3 treasure.py --num-nodes 5 --node-spacing 15 --behavior approach
    python3 treasure.py --mac aa:aa:aa:aa:aa:02 --behavior retreat --speed 2
"""
import argparse
import json
import math
import random
import time
import urllib.request

RSSI_AT_1M = -51.4
PATH_LOSS_EXPONENT = 2.45
NOISE_STD_DB = 3.7

JITTER_M = 0.3  # per-tick positional noise, meters


def rssi_for_distance(d):
    d = max(d, 0.1)  # avoid log(0) right on top of the node
    path_loss = 10 * PATH_LOSS_EXPONENT * math.log10(d)
    return round(RSSI_AT_1M - path_loss + random.gauss(0, NOISE_STD_DB))


def packet_count():
    return random.randint(1, 6)


def make_nodes(num_nodes, spacing):
    return [(chr(ord("A") + i), i * spacing) for i in range(num_nodes)]


def step_position(position, velocity, dt, bounds):
    position += velocity * dt + random.uniform(-JITTER_M, JITTER_M)
    lo, hi = bounds
    if position < lo:
        position, velocity = lo, abs(velocity)
    elif position > hi:
        position, velocity = hi, -abs(velocity)
    return position, velocity


def send_report(server, node, mac, distance):
    body = {
        "node": node,
        "uptime_ms": int(time.monotonic() * 1000),
        "readings": {mac: {"rssi": rssi_for_distance(distance), "n": packet_count()}},
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{server}/api/report", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            print(f"[{node}] dist={distance:5.1f}m sent=ok status={resp.status}")
    except Exception as e:
        print(f"[{node}] sent=FAILED ({e})")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="http://localhost:8080",
                     help="game server base URL (default: %(default)s)")
    ap.add_argument("--num-nodes", type=int, default=3,
                     help="how many nodes to simulate, named A, B, C... (default: %(default)s)")
    ap.add_argument("--node-spacing", type=float, default=10.0,
                     help="meters between adjacent nodes (default: %(default)s)")
    ap.add_argument("--behavior", choices=["approach", "retreat", "wander"], default="wander",
                     help="approach = walk toward the far node, retreat = walk toward "
                          "the near node, wander = jitter in place (default: %(default)s)")
    ap.add_argument("--speed", type=float, default=1.0,
                     help="walking speed in m/s for approach/retreat (default: %(default)s)")
    ap.add_argument("--mac", default="aa:aa:aa:aa:aa:01",
                     help="fake phone MAC to report (default: %(default)s)")
    ap.add_argument("--interval", type=float, default=1.0,
                     help="seconds between report rounds (default: %(default)s)")
    args = ap.parse_args()

    nodes = make_nodes(args.num_nodes, args.node_spacing)
    bounds = (0.0, nodes[-1][1]) if len(nodes) > 1 else (0.0, args.node_spacing)
    velocity = {"approach": args.speed, "retreat": -args.speed, "wander": 0.0}[args.behavior]
    position = (bounds[0] + bounds[1]) / 2

    print(f"nodes: {[(n, round(p, 1)) for n, p in nodes]}")
    print(f"behavior={args.behavior} speed={args.speed}m/s mac={args.mac} "
          f"-> {args.server} every {args.interval}s (Ctrl+C to stop)")

    try:
        while True:
            position, velocity = step_position(position, velocity, args.interval, bounds)
            for node, node_pos in nodes:
                send_report(args.server, node, args.mac, abs(position - node_pos))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("stopping...")


if __name__ == "__main__":
    main()
