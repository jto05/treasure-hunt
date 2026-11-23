import random
import time
import threading

from .base import Challenge
from ..state import GameStore
from ..proximity import STALE_AFTER_S

class DistThreshold(Challenge):
    """
    Dist Threshold: The team is given a distance they need to move away 
    from or closer to the node. They have 10 seconds to reach it.

    When the threshold is reached, the button to progres becomes available.
    
    If the team misses the deadline, they must wait 5 seconds as a penalty
    before they can try again.

    This goes on for 3 rounds in which each round will have a random RSSI
    threshold to get above or below.
    """

    def __init__(self, config: dict, node, store: GameStore):
        self.config = config
        self.node = node
        self.store = store

        # Check if received node or team mac addrs and rssi strengths.
        if self.node is None or self.store is None:
            raise ValueError("dist_threshold: needs node and store")

        # Keep thresshold reasonable.
        self.rounds = int(self.config.get("rounds", 3))
        self.min_rssi = float(self.config.get("min_rssi", -100))
        self.max_rssi = float(self.config.get("max_rssi", -25))

        if self.rounds != 3:
            raise ValueError("dist_threshold: rounds must be 3")

        if not -100 <= self.min_rssi <= self.max_rssi <= -25:
            raise ValueError("dist_threshold: RSSI range must be between -100 and -25 dBm")


        # Set time limit to 10s and penalty to 5s.
        self.time_limit = float(self.config.get("time_limit", 10))
        self.penalty = float(self.config.get("penalty", 5))
        if self.time_limit <= 0:
            raise ValueError("dist_threshold: time_limit must be > 0")
        if self.penalty < 0:
            raise ValueError("dist_threshold: penalty must be >= 0")

        # token = {"state", "started_at", "penalty_until", "latest"}
        # state changes between "running", "reached", "penalty", "done"
        self._teams = {}
        self._lock = threading.Lock()

    # ---- helpers -------------------------------------------------------

    # Check if threshold has been reached.
    def _is_met(self, rssi, t):
        if t["direction"] == "over":
            return rssi >= t["threshold"]

        return rssi <= t["threshold"]

    # Get node rssi readings to phone.
    def _reading(self, token):
        team = self.store.get_team(token)

        if team is None or not team.get("mac"):
            return None
        
        return self.store.get_readings(self.node).get(team["mac"])

    # Dist Threshold Game
    def _game_loop(self, t, token, now):
        reading = self._reading(token)

        # Check if signal is active.
        fresh = (reading is not None and now - reading["received_at"] <= STALE_AFTER_S)

        # Set current rssi measurement and threshold met status.
        rssi = reading["rssi"] if fresh else None
        met = fresh and self._is_met(rssi, t)

        # Update status.
        t["latest"] = {
            "signal": "ok" if fresh else "no_signal",
            "rssi": rssi,
            "met": met,
        }

        # Wait for penalty to end.
        if t["state"] == "penalty":
            if now < t["penalty_until"]:
                return

            # Penalty finished.
            self._start_round(t, now)
            return

        # Do nothing if challenge is not running.
        if t["state"] != "running":
            return

        # Set deadline to be 10s after round start.
        deadline = t["started_at"] + self.time_limit

        # Team reached threshold before time expired.
        if met and now <= deadline:
            t["state"] = "reached"
            return

        # Team missed deadline.
        if now > deadline:
            t["state"] = "penalty"
            t["penalty_until"] = now + self.penalty


    # Team game info.
    def _view(self, t, now):
        state = t["state"]
        signal = t["latest"]

        view = {
            "type": "dist_threshold",
            "round": t["round"],
            "rounds": self.rounds,
            "done": state == "done",
            "state": state,
            "can_press": state == "reached",
            "direction": t["direction"],
            "threshold": t["threshold"],
            "instruction": (
                "Get closer!" if t["direction"] == "over"
                else "Run away!"
            ),
            "signal": signal["signal"],
            "rssi": (round(signal["rssi"], 1) if signal["rssi"] is not None else None)
        }

        # Reset times.
        if state != "done":
            remaining = 0.0
            penalty_remaining = 0.0

            # Set threshold time.
            if state == "running":
                deadline = t["started_at"] + self.time_limit
                remaining = max(0.0, deadline - now)

            # Set penalty time.
            if state == "penalty":
                penalty_remaining = max(0.0, t["penalty_until"] - now)

            # Update.
            view.update({
                "met": signal["met"],
                "time_limit": self.time_limit,
                "remaining": round(remaining, 1),
                "penalty_remaining": round(penalty_remaining, 1),
            })

        return view

    def _start_round(self, t, now):
        if t["round"] == 1:
            direction = "over"
        elif t["round"] == 2:
            direction = "under"
        else:
            direction = "over"

        t["threshold"] = random.randint(int(self.min_rssi), int(self.max_rssi))
        t["direction"] = direction
        t["state"] = "running"
        t["started_at"] = now
        t["penalty_until"] = None
        t["latest"] = {
            "signal": "no_signal",
            "rssi": None,
            "met": False,
        }


    # ---- Challenge interface ------------------------------------------

    # Run the challenge.
    def start(self, token, now=None) -> dict:
        # Set curr time.
        now = time.time() if now is None else now

        # Stop teams from being updated out of order/twice.
        with self._lock:
            t = self._teams.get(token)

            # Give team challenge info.
            if t is None:
                t = {
                    "round": 1,
                    "state": "running",
                    "started_at": now,
                    "penalty_until": None,
                    "threshold": None,
                    "direction": None,
                    "latest": {"signal": "no_signal", 
                               "rssi": None,
                                 "met": False
                    },
                }
                self._teams[token] = t
                self._start_round(t, now)

            # Run game loop if not done.
            if t["state"] != "done":
                self._game_loop(t, token, now)

            return self._view(t, now)

    # Button press.
    def submit(self, token=None, answer=None, now=None) -> dict:
        # Set time.
        now = time.time() if now is None else now

        # Stop teams from being updated out of order/twice.
        with self._lock:
            t = self._teams.get(token)
            if t is None:
                return {"error": "not_started"}

            # "Correct" means press was successful.
            if t["state"] == "done":
                return {"correct": True, **self._view(t, now)}

            self._game_loop(t, token, now)

            if t["state"] == "penalty":
                return {"error": "locked"}
            
            if t["state"] != "reached":
                return {"error": "not_reached"}

            if t["round"] >= self.rounds:
                t["state"] = "done"

                return {
                    "correct": True,
                    ** self._view(t,now),
                }

            # Next round.
            t["round"] += 1
            self._start_round(t, now)

            return { 
                "correct": True,
                **self._view(t, now),
            }

    # Checks.

    def is_done(self, token):
        with self._lock:
            t = self._teams.get(token)
            return bool(t and t["state"] == "done")
        
    def reset(self, token):
        with self._lock:
            self._teams.pop(token, None)
