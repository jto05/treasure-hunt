import random
import threading

import pytest
from hunt.challenges import CHALLENGES, build
from hunt.challenges.memory_matrix import MemoryMatrix

CFG = {"rounds": 3, "start_length": 3, "colors": ["red", "green", "blue", "yellow"], "show_ms": 500}


def make(cfg=None, seed=1):
    return MemoryMatrix(dict(cfg or CFG), node="C", store=None, rng=random.Random(seed))


def wrong_answer(game, seq):
    # same length, guaranteed to differ in the first tile
    other = next(c for c in game.colors if c != seq[0])
    return [other] + seq[1:]


# ---- registry / build ----------------------------------------------------

def test_registered_in_challenges():
    assert CHALLENGES["memory_matrix"] is MemoryMatrix


def test_build_from_config_entry():
    game = build({"type": "memory_matrix", "rounds": 2})
    assert isinstance(game, MemoryMatrix)
    assert game.rounds == 2


def test_defaults_when_config_empty():
    game = MemoryMatrix({})
    assert game.rounds == 3
    assert game.start_length == 3
    assert game.colors == ["red", "green", "blue", "yellow"]


@pytest.mark.parametrize("bad", [{"rounds": 0}, {"start_length": 0}, {"colors": ["red"]}])
def test_rejects_bad_config(bad):
    with pytest.raises(ValueError):
        MemoryMatrix(bad)


# ---- start ---------------------------------------------------------------

def test_start_returns_round_one_sequence():
    game = make()
    s = game.start("t1")
    assert s["round"] == 1
    assert s["rounds"] == 3
    assert s["done"] is False
    assert s["show_ms"] == 500
    assert len(s["sequence"]) == 3
    assert all(c in CFG["colors"] for c in s["sequence"])


def test_start_is_idempotent():
    game = make()
    first = game.start("t1")
    again = game.start("t1")
    assert again == first


# ---- submit --------------------------------------------------------------

def test_correct_answers_advance_rounds_and_finish():
    game = make()
    seq = game.start("t1")["sequence"]

    r = game.submit("t1", seq)
    assert r["correct"] is True and r["done"] is False
    assert r["round"] == 2 and len(r["sequence"]) == 4

    r = game.submit("t1", r["sequence"])
    assert r["round"] == 3 and len(r["sequence"]) == 5

    r = game.submit("t1", r["sequence"])
    assert r["correct"] is True and r["done"] is True
    assert "sequence" not in r
    assert game.is_done("t1")


def test_wrong_answer_keeps_round_and_changes_sequence():
    game = make()
    seq = game.start("t1")["sequence"]
    game.submit("t1", seq)  # now round 2
    seq2 = game.start("t1")["sequence"]

    r = game.submit("t1", wrong_answer(game, seq2))
    assert r["correct"] is False
    assert r["done"] is False
    assert r["round"] == 2
    assert len(r["sequence"]) == 4
    # the old sequence is no longer accepted -- only the new one is
    assert game.start("t1")["sequence"] == r["sequence"]


def test_answer_is_case_and_space_insensitive():
    game = make()
    seq = game.start("t1")["sequence"]
    r = game.submit("t1", [f" {c.upper()} " for c in seq])
    assert r["correct"] is True


def test_wrong_length_is_wrong_not_error():
    game = make()
    seq = game.start("t1")["sequence"]
    r = game.submit("t1", seq[:-1])
    assert r["correct"] is False


def test_submit_before_start():
    assert make().submit("nobody", ["red"]) == {"error": "not_started"}


@pytest.mark.parametrize("bad", [None, "red,green", 3, ["red", 1], {"a": 1}])
def test_malformed_answer_changes_nothing(bad):
    game = make()
    before = game.start("t1")
    assert game.submit("t1", bad) == {"error": "bad_answer"}
    assert game.start("t1") == before


def test_submit_after_done_stays_done():
    game = make({"rounds": 1, "start_length": 2})
    seq = game.start("t1")["sequence"]
    assert game.submit("t1", seq)["done"] is True
    r = game.submit("t1", ["whatever"])
    assert r["done"] is True and r["correct"] is True


# ---- multiple teams ------------------------------------------------------

def test_teams_are_independent():
    game = make()
    a = game.start("team_a")["sequence"]
    game.start("team_b")

    game.submit("team_a", a)  # team_a -> round 2
    assert game.start("team_a")["round"] == 2
    assert game.start("team_b")["round"] == 1

    # team_b can't use team_a's progress
    assert game.submit("team_b", wrong_answer(game, game.start("team_b")["sequence"]))["correct"] is False
    assert game.start("team_b")["round"] == 1


def test_reset_clears_one_team():
    game = make()
    game.start("t1")
    game.start("t2")
    game.reset("t1")
    assert game.submit("t1", ["red"]) == {"error": "not_started"}
    assert "error" not in game.start("t2")


def test_concurrent_teams_do_not_interfere():
    game = make({"rounds": 5, "start_length": 2})
    tokens = [f"t{i}" for i in range(20)]
    errors = []

    def play(tok):
        try:
            seq = game.start(tok)["sequence"]
            for _ in range(5):
                r = game.submit(tok, seq)
                assert r["correct"]
                seq = r.get("sequence")
            assert game.is_done(tok)
        except Exception as e:  # noqa: BLE001 - re-raised via the assert below
            errors.append(e)

    threads = [threading.Thread(target=play, args=(t,)) for t in tokens]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
