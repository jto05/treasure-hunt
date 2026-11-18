import random
import threading

from .base import Challenge


class MemoryMatrix(Challenge):
    """
    Memory Matrix (Simon Says style) -- the phone shows a sequence of
    colored tiles, the player taps them back in order.

    The server owns everything that matters: it generates each sequence,
    keeps it per team (keyed by the team token), checks every answer and
    decides when the challenge is done. The phone only displays the
    sequence it is given and sends back what the player tapped.

    config.json entry (all fields except "type" are optional):

        "C": {"type": "memory_matrix",
              "rounds": 3,
              "start_length": 3,
              "colors": ["red", "green", "blue", "yellow"],
              "show_ms": 700}

    Round r uses a sequence of start_length + (r - 1) colors, so the
    defaults above give lengths 3, 4, 5.

    A wrong answer keeps the team on the same round and gives them a
    fresh sequence of the same length (it does not reset to round 1).
    """

    DEFAULT_COLORS = ("red", "green", "blue", "yellow")

    def __init__(self, config, node=None, store=None, rng=None):
        # Set these directly instead of calling super().__init__ so this
        # works with both base.py versions: master's (no __init__) and
        # feat/challenge-template's (config, node, store).
        self.config = config
        self.node = node
        self.store = store

        self.rounds = int(config.get("rounds", 3))
        self.start_length = int(config.get("start_length", 3))
        self.colors = [c.strip().lower() for c in config.get("colors", self.DEFAULT_COLORS)]
        self.show_ms = int(config.get("show_ms", 700))

        if self.rounds < 1:
            raise ValueError("memory_matrix: rounds must be >= 1")
        if self.start_length < 1:
            raise ValueError("memory_matrix: start_length must be >= 1")
        if len(self.colors) < 2:
            raise ValueError("memory_matrix: need at least 2 colors")

        # tests pass a seeded random.Random so sequences are predictable
        self._rng = rng or random.SystemRandom()

        # token -> {"round", "sequence", "done", "attempts"}
        # Waitress serves on several threads, so guard it with a lock.
        self._teams = {}
        self._lock = threading.Lock()

    # ---- helpers -------------------------------------------------------

    def _length_for(self, round_no):
        return self.start_length + round_no - 1

    def _new_sequence(self, round_no):
        return [self._rng.choice(self.colors) for _ in range(self._length_for(round_no))]

    def _view(self, t):
        # what the phone gets back; never includes anything it shouldn't
        # need beyond the sequence it has to display
        view = {
            "type": "memory_matrix",
            "round": t["round"],
            "rounds": self.rounds,
            "done": t["done"],
            "colors": self.colors,
            "show_ms": self.show_ms,
        }
        if not t["done"]:
            view["sequence"] = list(t["sequence"])
        return view

    # ---- Challenge interface ------------------------------------------

    def start(self, token) -> dict:
        """
        Start the challenge for this team, or return where they already
        are. Calling it again (e.g. the page was refreshed) does NOT
        generate a new sequence.
        """
        with self._lock:
            t = self._teams.get(token)
            if t is None:
                t = {
                    "round": 1,
                    "sequence": self._new_sequence(1),
                    "done": False,
                    "attempts": 0,
                }
                self._teams[token] = t
            return self._view(t)

    def submit(self, token, answer) -> dict:
        """
        answer: list of color strings, e.g. ["red", "blue", "red"].

        Returns {"correct", "done", "round", "rounds", ...}. When not done,
        "sequence" is the sequence to show next (the next round's on a
        correct answer, a fresh one for the same round on a wrong answer).
        Returns {"error": ...} for a submit before start or a malformed
        answer, without changing anything.
        """
        if not isinstance(answer, list) or not all(isinstance(a, str) for a in answer):
            return {"error": "bad_answer"}

        with self._lock:
            t = self._teams.get(token)
            if t is None:
                return {"error": "not_started"}

            if t["done"]:
                # already finished -- re-submitting changes nothing
                return {"correct": True, **self._view(t)}

            t["attempts"] += 1
            correct = [a.strip().lower() for a in answer] == t["sequence"]

            if correct:
                if t["round"] >= self.rounds:
                    t["done"] = True
                else:
                    t["round"] += 1
                    t["sequence"] = self._new_sequence(t["round"])
            else:
                # same round, new sequence
                t["sequence"] = self._new_sequence(t["round"])

            return {"correct": correct, **self._view(t)}

    # optional extras -- not part of base.Challenge, handy for admin/tests

    def is_done(self, token):
        with self._lock:
            t = self._teams.get(token)
            return bool(t and t["done"])

    def reset(self, token):
        with self._lock:
            self._teams.pop(token, None)
