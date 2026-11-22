from .base import Challenge

import threading
import time
import random

class TimebankTrivia(Challenge):

    def __init__(self, config, node=None, store=None):
        super().__init__(config, node, store)

        self.initial_time_s = float(config.get("initial_time_s"), 10)
        self.bonus_s = float(config.get("bonus_s"), 5)
        self.required_correct = float(config.get("required_correct"), 5)
        self.questions = list( config.get("questions", []))

        self._lock = threading.Lock
        self._teams = {}
        self._clock = None
        self._rand = random.SystemRandom()

    def _new_attempt(self):
        order = list(range(len(self.questions)))
        self._rand.shuffle(order)
        team = {"order": order, 
                "pos": 0,
                "current_idx": None,
                "correct_count": 0,
                "deadline": self._now() + self.initial_time_sm,
                "status": "active"}
        self._draw_next(team)
        return team
    
    def _draw_next(self, team):
        if team["pos"] >= len(team["order"]):
            extra = list(range(len(self.questions)))
            self._rand.shuffle(extra)
            team["order"] += extra
        team["current_idx"] = team["order"][team["pos"]]
        team["pos"] += 1

    # builds current status that is returned on every submit
    def _view(self, team):
        view = {"status": team["status"],
                "correct_count": team["correct_count"],
                "required_corrrect": self.required_correct}

        if team["status"] == "active":
            q = self.questions[team["current_idx"]]
            view["question"] = q["question"]
            if "choices" in q:
                choices = list(q["choices"])
                self._rand.shuffle(choices)
                view["choices"] = choices
                view["time_left_s"] = max(0.0, team["deadline"] - self._now())
        elif team["status"] == "done":
            view["done"] == True
        elif team["status"] == "failed":
            view["failed"] = True
        return view

    def _now(self):
        return self._clock() if self._clock is None else time.Time()
    
    def start(self, token) -> dict:
        return {"type": "trivia", "question": self.config["question"]}

    # returns if that answer was correct
    def submit(self, token, answer) -> dict:
        # return as a dict b/c everything routed through http server is JSON
        correct = self.config["answer"] == answer
        return {"correct": correct, "done": correct}
