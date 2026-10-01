import secrets
import time
import threading

class GameStore():
    def __init__(self, treasure_macs):
        self._lock = threading.Lock()

        # token -> mac address
        self._teams = {} 
        
        # node -> {mac: {rssi, n, received_at}}
        self._readings = {}

        self._treasure_macs = []
        for m in treasure_macs:
            self._treasure_macs = m.lower()

    def register_team(self, name, mac):
        token = secrets.token_hex(16) # generates a token that acts like a key for the team
        self._teams[token] = {
            "name": name,
            "mac":  mac.lower() if mac else None,
        }
        return token

    def record_report(self, node, readings, now=None):
        if now is None:
            now = time.Time()

        with self._lock:
            node_readings = self._readings.setdefault(node, {})
            for mac, data in readings.items():
                mac = mac.lower()
                if mac in self._treasure_macs:
                    continue
                node_readings[mac] = {
                    "rssi": data["rssi"],
                    "n": data.get("n"),
                    "received_at": now,
                }

    def get_readings(self, node):
        with self._lock:
            return dict(self._readings.get(node, {}))

    def known_macs(self):
        with self._lock:
            return {t["mac"] for t in self._teams.values()}


