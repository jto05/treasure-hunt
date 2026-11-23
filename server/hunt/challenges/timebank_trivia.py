from .base import Challenge

import threading
import time
import random


class TimebankTrivia(Challenge):
    """
    Timebank Trivia -- the team shares one countdown ("time bank") instead
    of a per-question timer. Every correct answer adds bonus_s back to the
    bank; wrong answers add nothing, but the question still advances (no
    retries). Reach required_correct before the bank hits zero to clear
    the node.

    config.json entry:
        "A": {"type": "timebank_trivia",
              "initial_time_s": 10, "bonus_s": 5, "required_correct": 5,
              "questions": [
                {"question": "...", "answer": "..."},                   # free-text
                {"question": "...", "choices": [...], "answer": "..."}  # multiple-choice
              ]}

    A question is multiple-choice iff it has a "choices" key. "answer" is
    always plain text, matched case/whitespace-insensitively; for
    multiple-choice questions it must match one of "choices" the same way.
    """

    def __init__(self, config, node=None, store=None, rng=None, clock=None):
        super().__init__(config, node, store)

        # default inside .get() -- float()/int() only take ONE argument,
        # so float(config.get("x"), 10) would crash with a missing "x"
        self.initial_time_s = float(config.get("initial_time_s", 10))
        self.bonus_s = float(config.get("bonus_s", 5))
        # a count of correct answers, not a duration -- int, not float
        self.required_correct = int(config.get("required_correct", 5))
        self.questions = list(config.get("questions", []))

        # validate config up front so a bad config.json fails loudly at
        # startup instead of crashing confusingly mid-game later
        if not self.questions:
            raise ValueError("timebank_trivia: need at least 1 question")
        if self.required_correct < 1:
            raise ValueError("timebank_trivia: required_correct must be >= 1")
        if self.initial_time_s <= 0:
            raise ValueError("timebank_trivia: initial_time_s must be > 0")
        if self.bonus_s < 0:
            raise ValueError("timebank_trivia: bonus_s must be >= 0")
        for q in self.questions:
            if not q.get("question") or "answer" not in q:
                raise ValueError("timebank_trivia: each question needs 'question' and 'answer'")
            if "choices" in q:
                choices = q["choices"]
                if not isinstance(choices, list) or len(choices) < 2 or \
                   not all(isinstance(c, str) and c.strip() for c in choices):
                    raise ValueError("timebank_trivia: 'choices' needs >= 2 non-empty strings")
                normalized = {c.strip().lower() for c in choices}
                if str(q["answer"]).strip().lower() not in normalized:
                    raise ValueError("timebank_trivia: 'answer' must match one of 'choices'")

        # tests inject a seeded random.Random / fake clock for determinism;
        # production just uses real randomness and the real wall clock
        self._rand = rng or random.SystemRandom()
        self._clock = clock
        self._teams = {}
        # Waitress serves on several threads, so guard shared state with a lock.
        self._lock = threading.Lock()

    # ---- helpers -------------------------------------------------------

    def _now(self):
        # never cache time.time as a bound reference -- look it up live so
        # tests can monkeypatch the module's `time.time` at any point, even
        # after this instance already exists
        return self._clock() if self._clock is not None else time.time()

    def _new_attempt(self):
        # fresh shuffled run through the question pool for a brand new team
        order = list(range(len(self.questions)))
        self._rand.shuffle(order)
        team = {"order": order,
                "pos": 0,
                "current_idx": None,
                "correct_count": 0,
                "deadline": self._now() + self.initial_time_s,
                "status": "active"}
        self._draw_next(team)
        return team

    def _draw_next(self, team):
        # pull the next question off the shuffled order; if we've used up
        # the whole pool mid-attempt, reshuffle a fresh lap and keep going
        # instead of crashing on an empty pool
        if team["pos"] >= len(team["order"]):
            extra = list(range(len(self.questions)))
            self._rand.shuffle(extra)
            team["order"] += extra
        team["current_idx"] = team["order"][team["pos"]]
        team["pos"] += 1

    def _expire_if_needed(self, token, team):
        # lazy timeout check -- there's no status/poll endpoint, so every
        # start()/submit() call checks "has the deadline passed?" first,
        # before doing anything else
        if team["status"] == "active" and self._now() >= team["deadline"]:
            self._on_failure(token, team)

    def _on_failure(self, token, team):
        """EXTENSION SEAM -- only this method's body should change if a
        different timeout mechanic gets designed later (partial credit,
        an extra life, etc). Current default: hard terminal failure,
        mirroring how MemoryMatrix treats "done" as final."""
        team["status"] = "failed"

    # builds the status dict returned on every start/submit call
    def _view(self, team):
        view = {"status": team["status"],
                "correct_count": team["correct_count"],
                "required_correct": self.required_correct}

        if team["status"] == "active":
            q = self.questions[team["current_idx"]]
            view["question"] = q["question"]
            if "choices" in q:
                # reshuffle on every view (not stored) -- grading is by
                # text match, so display order never affects correctness
                choices = list(q["choices"])
                self._rand.shuffle(choices)
                view["choices"] = choices
            # time_left_s applies to every active question, not just MC ones
            view["time_left_s"] = max(0.0, team["deadline"] - self._now())
        elif team["status"] == "done":
            view["done"] = True
        elif team["status"] == "failed":
            view["failed"] = True
        return view

    # ---- Challenge interface ------------------------------------------

    def start(self, token) -> dict:
        with self._lock:
            team = self._teams.get(token)
            if team is None:
                # first time this team hits the node -- start a fresh attempt
                team = self._teams[token] = self._new_attempt()
            else:
                # idempotent: re-calling start (e.g. page refresh) never
                # regenerates state, it just re-checks the clock
                self._expire_if_needed(token, team)
            return self._view(team)

    def submit(self, token, answer) -> dict:
        # reject malformed answers before touching any state
        if not isinstance(answer, (str, type(None))):
            return {"error": "bad_answer"}

        with self._lock:
            team = self._teams.get(token)
            if team is None:
                return {"error": "not_started"}

            # the clock is checked before grading anything -- if time ran
            # out, this submit doesn't count even if the answer was right
            self._expire_if_needed(token, team)
            if team["status"] != "active":
                # terminal state (done or failed) -- resubmitting changes nothing
                return {"correct": team["status"] == "done",
                        **self._view(team)}

            correct = (isinstance(answer, str) and
                       answer.strip().lower() == str(self.questions[team["current_idx"]]["answer"]).strip().lower())

            if correct:
                team["correct_count"] += 1
                team["deadline"] += self.bonus_s
                if team["correct_count"] >= self.required_correct:
                    team["status"] = "done"
                    return {"correct": True, **self._view(team)}
            # wrong OR correct-but-not-done yet: advance to the next
            # question either way -- no retrying the same one
            self._draw_next(team)
            return {"correct": correct, **self._view(team)}

    # optional extras -- not part of base.Challenge, handy for admin/tests

    def is_done(self, token):
        with self._lock:
            team = self._teams.get(token)
            return bool(team and team["status"] == "done")

    def reset(self, token):
        with self._lock:
            self._teams.pop(token, None)
