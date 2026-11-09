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

Each simulated phone's distance to each node does a small random walk
every tick, so readings actually drift instead of sitting still.

Deliberately ignores /api/report's watch_macs reply and the whole
team-registration flow: on a dev machine (no dnsmasq), a real team
registration always resolves to mac=None, so watch_macs would always come
back empty and nothing would ever get reported. This just keeps the
server fed unconditionally instead.

Usage:
    python3 treasure.py
    python3 treasure.py --server http://10.42.0.1:8080 --nodes A,B --interval 1
"""
import argparse
import json
import math
import random
import threading
import time
import urllib.request

RSSI_AT_1M = -51.4
PATH_LOSS_EXPONENT = 2.45
NOISE_STD_DB = 3.7

# mac -> {node: starting distance in meters}
DEFAULT_PHONES = {
    "aa:aa:aa:aa:aa:01": {"A": 2.0, "B": 6.0, "C": 12.0},
    "aa:aa:aa:aa:aa:02": {"A": 9.0, "B": 3.0, "C": 7.0},
}


def rssi_for_distance(d):
    d = max(d, 0.1)  # avoid log(0) right on top of the node
    path_loss = 10 * PATH_LOSS_EXPONENT * math.log10(d)
    return round(RSSI_AT_1M - path_loss + random.gauss(0, NOISE_STD_DB))


def packet_count():
    return random.randint(1, 6)


def wander(distance, step=0.3, bounds=(0.5, 20.0)):
    distance += random.uniform(-step, step)
    return min(max(distance, bounds[0]), bounds[1])


def send_report(server, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{server}/api/report", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            print(f"[{body['node']}] sent=ok macs={len(body['readings'])} status={resp.status}")
    except Exception as e:
        print(f"[{body['node']}] sent=FAILED ({e})")


def node_loop(node, server, phones, interval, stop):
    distances = {mac: dists[node] for mac, dists in phones.items() if node in dists}
    start = time.monotonic()

    while not stop.is_set():
        readings = {}
        for mac in distances:
            distances[mac] = wander(distances[mac])
            readings[mac] = {"rssi": rssi_for_distance(distances[mac]), "n": packet_count()}

        send_report(server, {
            "node": node,
            "uptime_ms": int((time.monotonic() - start) * 1000),
            "readings": readings,
        })
        stop.wait(interval)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="http://localhost:8080",
                     help="game server base URL (default: %(default)s)")
    ap.add_argument("--nodes", default="A,B,C",
                     help="comma-separated node letters to simulate (default: %(default)s)")
    ap.add_argument("--interval", type=float, default=1.0,
                     help="seconds between reports per node (default: %(default)s)")
    args = ap.parse_args()

    nodes = args.nodes.split(",")
    stop = threading.Event()
    threads = [
        threading.Thread(target=node_loop,
                          args=(node, args.server, DEFAULT_PHONES, args.interval, stop),
                          daemon=True)
        for node in nodes
    ]

    print(f"simulating nodes {nodes} -> {args.server} every {args.interval}s (Ctrl+C to stop)")
    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("stopping...")
        stop.set()
        for t in threads:
            t.join()


if __name__ == "__main__":
    main()
