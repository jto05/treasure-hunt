"""
End-to-end check of Memory Matrix through the real Flask routes, with no
Pi and no ESP32: tests/fake.leases maps 127.0.0.1 (the test client's IP)
to a fake MAC so POST /api/team works.
"""
import os

import pytest

SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("LEASES_PATH", os.path.join(SERVER_DIR, "tests", "fake.leases"))
    monkeypatch.chdir(SERVER_DIR)  # load_config() reads config.json from cwd
    from app import create_app

    app = create_app()
    app.testing = True
    return app


def register(app, name):
    c = app.test_client()
    r = c.post("/api/team", json={"name": name})
    assert r.status_code == 200, r.get_json()
    return c


def team_on_node(app, node):
    # progression rotates paths A,B,C / B,C,A / C,A,B -- register teams
    # until one starts on the node we want
    for i in range(3):
        c = register(app, f"team{i}")
        if c.get("/api/state").get_json()["node"] == node:
            return c
    raise AssertionError(f"no team started on {node}")


def test_full_memory_matrix_flow_completes_node(client):
    c = team_on_node(client, "C")

    r = c.post("/api/challenge/C/start")
    assert r.status_code == 200
    body = r.get_json()
    seq = body["sequence"]

    # wrong answer: same round, still on node C
    r = c.post("/api/challenge/C/submit", json={"answer": ["nope"] * len(seq)})
    assert r.get_json()["correct"] is False
    seq = r.get_json()["sequence"]

    for _ in range(body["rounds"]):
        r = c.post("/api/challenge/C/submit", json={"answer": seq})
        data = r.get_json()
        assert data["correct"] is True
        seq = data.get("sequence")

    assert data["done"] is True
    state = c.get("/api/state").get_json()
    assert state["progress"]["step"] == 1
    assert state["node"] != "C"


def test_wrong_node_is_rejected(client):
    c = team_on_node(client, "A")
    assert c.post("/api/challenge/C/start").status_code == 403


def test_bad_answer_is_400(client):
    c = team_on_node(client, "C")
    c.post("/api/challenge/C/start")
    r = c.post("/api/challenge/C/submit", json={"answer": "red"})
    assert r.status_code == 400
    assert r.get_json() == {"error": "bad_answer"}


def test_node_without_challenge_is_404(client):
    c = team_on_node(client, "B")
    assert c.post("/api/challenge/B/start").status_code == 404


def test_unregistered_is_401(client):
    assert client.test_client().post("/api/challenge/C/start").status_code == 401
