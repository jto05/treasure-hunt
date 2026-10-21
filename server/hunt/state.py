import logging
import secrets
import time
import threading

logger = logging.getLogger(__name__)

# Weight given to a new RSSI sample vs. the previously smoothed value:
#   alpha = n / (n + RSSI_SMOOTHING_K)
# n = packets this MAC was heard on since the last report (sent by the
# ESP32). More packets this interval -> higher alpha -> trust the new
# sample more. n=0 -> alpha=0 -> keep the old smoothed value unchanged,
# which is the right behavior for a stale-but-not-yet-expired reading.
# 5 is a starting guess -- retune once real hardware is reporting, this
# can't be tuned meaningfully without live RSSI data.
RSSI_SMOOTHING_K = 5


class GameStore():
    def __init__(self, treasure_macs):
        self._lock = threading.Lock()

        # token -> mac address
        self._teams = {} 
        
        # node -> {mac: {rssi, n, received_at}}
        self._readings = {}

        self._treasure_macs = []
        for m in treasure_macs:
            self._treasure_macs.append(m.lower())

    def register_team(self, name, mac):
        name = name.strip()
        with self._lock:
            for team in self._teams.values(): # prevent duplicate team names
                if team["name"].lower() == name.lower():
                    return None

            token = secrets.token_hex(16) # generates a token that acts like a key for the team
            self._teams[token] = {
                "name": name,
                "mac":  mac.lower() if mac else None,
            }
        return token

    def record_report(self, node, readings, now=None):
        if now is None:
            now = time.time()

        with self._lock:
            node_readings = self._readings.setdefault(node, {})
            for mac, data in readings.items():
                mac = mac.lower()
                if mac in self._treasure_macs:
                    logger.debug("ignoring treasure mac %s on node %s", mac, node)
                    continue

                raw_rssi = data["rssi"]
                n = data.get("n") or 0
                previous = node_readings.get(mac)
                if previous is None:
                    # first-ever reading for this mac -- nothing to blend with
                    smoothed_rssi = raw_rssi
                else:
                    alpha = n / (n + RSSI_SMOOTHING_K)
                    smoothed_rssi = alpha * raw_rssi + (1 - alpha) * previous["rssi"]

                node_readings[mac] = {
                    "rssi": smoothed_rssi,
                    "n": data.get("n"),
                    "received_at": now,
                }

    def get_readings(self, node):
        with self._lock:
            return dict(self._readings.get(node, {}))

    def all_readings(self):
        with self._lock:
            return {node: dict(readings) for node, readings in self._readings.items()}

    def teams(self):
        """[{"name", "mac"}, ...]"""
        with self._lock:
            return [{"name": t["name"], "mac": t["mac"]} for t in self._teams.values()]


    def known_macs(self):
        with self._lock:
            macs = []
            for team in self._teams.values():
                if team["mac"] is None:
                    continue
                macs.append(team["mac"])
            return macs

    def get_team(self, token): # when a person refreshes there page, get their team based on cookies
        if not token:
            return None
        with self._lock:
            team = self._teams.get(token)
            return dict(team) if team else None



