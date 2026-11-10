import threading
import time

class Progression:
    def __init__(self, nodes):
        self._nodes = list(nodes)
        self._lock = threading.Lock()
        self._progress = {}
        self._count = 0

    #randomize the node path per each team
    def make_path(self):
        rotate = self._count % len(self._nodes)
        return self._nodes[rotate:] + self._nodes[:rotate]

    #assigning a node path to a team
    def start(self, token, now=None):
        with self._lock:
            if token in self._progress:
                return
            self._progress[token] = {
                "path": self.make_path(),
                "step": 0,
                "started_at": now or time.time(),
                "finished_at": None,
            }
            self._count += 1

    #get which node is next
    def current_node(self, token):
        with self._lock:
            p = self._progress.get(token)
            if p is None or p["step"] >= len(p["path"]):
                return None
            return p["path"][p["step"]]

    #advance progress
    def complete(self, token, node, now=None):
        with self._lock:
            p = self._progress.get(token)
            if p is None or p["step"] >= len(p["path"]):
                return False
            if p["path"][p["step"]] != node: #not at the right node
                return False
            p["step"] += 1
            if p["step"] == len(p["path"]): #at the last node
                p["finished_at"] = now or time.time()
            return True

    #for front end
    def summary(self, token):
        with self._lock:
            p = self._progress.get(token)
            if p is None:
                return None
            return {
                "step" : p["step"],
                "total" : len(p["path"]),
                "finished" : p["finished_at"] is not None,
            }

    #mayb for admin view?? 
    def leaderboard(self):
        with self._lock:
            rows = [
                (t, p["step"], p["started_at"], p["finished_at"])
                for t, p in self._progress.items()
            ]

        rows.sort(key = lambda r: (-r[1], r[3] or r[2]))
        return rows
                           
