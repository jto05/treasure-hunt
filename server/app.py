import ipaddress
import logging
import os

from flask import Flask, jsonify, request, send_from_directory
from hunt.config import load_config
from hunt.logging_setup import configure_logging
from hunt.netinfo import ip_to_mac
from hunt.state import GameStore
from hunt.proximity import describe
from hunt.progression import Progression
from hunt.challenges import build

WEB_DIR = os.environ.get("WEB_DIR", os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))


def _client_ip(req):
    # the Vite dev proxy (frontend/vite.config.js, xfwd: true) sets this
    # to the real device's IP -- without it, req.remote_addr would just
    # be the proxy's own loopback connection. Trusting this header is
    # fine here: the only thing ever in front of Flask is that proxy, on
    # an isolated AP with no other client able to reach it directly.
    forwarded = req.headers.get("X-Forwarded-For")
    raw = forwarded.split(",")[0].strip() if forwarded else req.remote_addr
    return _normalize_ip(raw)


def _normalize_ip(raw):
    # a dual-stack socket (e.g. Vite's dev server) reports an IPv4 client
    # as IPv4-mapped IPv6 (::ffff:a.b.c.d) -- dnsmasq.leases only ever has
    # plain IPv4, so unwrap it back to that when present.
    try:
        addr = ipaddress.ip_address(raw)
    except ValueError:
        return raw  # not a parseable IP at all -- pass through as-is

    mapped = getattr(addr, "ipv4_mapped", None)
    return str(mapped) if mapped else str(addr)

# /admin hasn't been ported into the React app yet -- it still lives in
# the old static web/ directory, which is not WEB_DIR (that's the React
# build output now). Point it there directly until it's ported.
LEGACY_WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")


def create_app():
    configure_logging()
    logger = logging.getLogger(__name__)

    app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")
    config = load_config()

    # build challenges
    challenges = {}
    for node, cfg in config.get("challenges", {}).items():
        challenges[node] = build(cfg)
        

    store = GameStore(treasure_macs = config["treasure_macs"])
    NODES = ["A", "B", "C"]
    progression = Progression(NODES)


    # Treasure reports the average RSSI per phone MAC address to server
    # every few seconds
    #
    # Expected JSON body from the ESP32:
    # {
    #   "node": "B",                # which treasure: "A", "B" or "C"
    #   "uptime_ms": 523000,        # optional, ESP32's own uptime
    #   "readings": {
    #     "a4:5e:60:12:34:56": {"rssi": -58, "n": 14, "age_ms": 200},
    #     "3c:22:fb:ab:cd:ef": {"rssi": -71, "n": 3,  "age_ms": 1800}
    #   }
    # }
    # readings is keyed by phone MAC address (lowercase). rssi is the
    # ESP32's raw last-sample dBm for this report interval -- smoothing
    # across reports happens server-side (GameStore.record_report), not
    # on the ESP32. n is packets heard for this mac since the ESP32's
    # last report (not optional -- the smoothing weight depends on it,
    # see RSSI_SMOOTHING_K in hunt/state.py). age_ms is how long ago
    # that MAC was last heard. Only MACs heard in the last 5s should be
    # included.
    @app.post("/api/report")
    def report():
        data = request.get_json()

        # check if bad json
        bad_json = not data or "node" not in data or "readings" not in data
        if bad_json:
            logger.warning("bad report body: %r", data)
            return jsonify({"error": "bad_json"}), 400

        # report readings
        store.record_report(data["node"], data["readings"])
        logger.info("report node=%s macs=%d", data["node"], len(data["readings"]))

        # return list of know_macs
        return jsonify({
            "ok": True,
            "watch_macs": store.known_macs()
        })

    # Register a team
    @app.post("/api/team")
    def register_team():
        client_ip = _client_ip(request)

        existing = store.get_team(request.cookies.get("team"))
        if existing:
            return jsonify({"team": existing["name"]})

        data = request.get_json(silent=True)
        if not data or not isinstance(data.get("name"), str):
            logger.warning("bad team registration body: %r ip=%s", data, client_ip)
            return jsonify({"error": "bad_json"}), 400

        name = data["name"].strip()
        if not name or len(name) > 20:
            logger.warning("bad team name: %r ip=%s", name, client_ip)
            return jsonify({"error": "bad_name"}), 400

        # get mac address from ip
        mac = ip_to_mac(client_ip)
        if mac is None:
            logger.warning("no mac found for ip %s", client_ip)
            return jsonify({"error":"mac_not_found"}), 400

        # build response
        token = store.register_team(data["name"], mac)
        if token is None:
            logger.info("team name already taken: %r ip=%s", data["name"], client_ip)
            return jsonify({"error": "name_taken"}), 409

        progression.start(token)
        logger.info("team registered name=%r mac=%s", data["name"], mac)
        resp = jsonify({"team": data["name"]})
        # build cookie that lets player's session persist
        resp.set_cookie("team", token, httponly=True, samesite="Lax",max_age=86400)
        return resp

    # advance from completeing one node to the next
    @app.post("/api/advance")
    def advance():
        token = request.cookies.get("team")
        team = store.get_team(token)
        if team is None:
            return jsonify({"error": "not_registered"}), 401

        node = progression.current_node(token)
        if node is None:
            return jsonify({"error": "finished"}), 400

        #get reading from server, not browser!! users cant be trusted
        reading = store.get_readings(node).get(team["mac"])
        if not describe(reading).get("in_range"):
            return jsonify({"error": "too_far"}), 403
        
        progression.complete(token, node)
        return jsonify({"ok": True})

    # Deregister a team
    @app.delete("/api/team")
    def deregister_team():
        token = request.cookies.get("team")
        if not token:
            return jsonify({"error": "not registered"}), 400
        
        removed = store.deregister_team(token)
        logger.info("team deregistered token=%s removed=%s", token, removed)

        resp = jsonify({"ok": True})
        resp.delete_cookie("team")
        return resp

    # Get the description of minigame at specific node
    @app.get("/api/challenge/<node>")
    def get_challenge(node):
        return jsonify()

    # Start challenge at specific node
    @app.post("/api/challenge/<node>/start")
    def start_challenge(node):
        token = request.cookies.get("team")
        team = store.get_team(token)
        if team is None:
            return jsonify({"error": "not_registered"}), 401
        if node != progression.current_node(token):
            return jsonify({"error": "wrong_node"}), 403

        # start respective challenge and return result
        return jsonify(challenges[node].start(token))

    # Submit an answer to the challenge at a specific node
    @app.post("/api/challenge/<node>/submit")
    def submit_challenge(node):
        token = request.cookies.get("team")
        team = store.get_team(token)
        if team is None:
            return jsonify({"error": "not_registered"}), 401
        if node != progression.current_node(token):
            return jsonify({"error": "wrong_node"}), 403

        data = request.get_json(silent=True) or {}
        result = challenges[node].submit(token, data.get("answer"))

        # NOTE: Automaticaly progress if it was correct is optional
        # if result.get("correct"):
        #     progression.complete(token, node)
        return jsonify(result)

    # Get leaderboard
    @app.get("/api/leaderboard")
    def leaderboard():
        rows = []
        for token, step, started_at, finished_at in progression.leaderboard_rows():
            team = store.get_team(token)
            if team is None:
                continue
            rows.append({
                "team": team["name"],
                "step": step,
                "total": len(NODES),
                "finished": finished_at is not None,
                "seconds": round(finished_at - started_at) if finished_at else None,
            })
        return jsonify({"leaderboard": rows})

    # rough testing pages -- just static files served from web/
    @app.get("/register")
    def register_page():
        return send_from_directory(WEB_DIR, "index.html")

    # NOTE: only for testing, maybe add some auth later on if we fancy :p
    @app.get("/admin/status")
    def admin_status():
        return jsonify({
            "nodes": store.all_readings(),
            "teams": store.teams()
        })

    @app.get("/admin")
    def admin_page():
        return send_from_directory(LEGACY_WEB_DIR, "admin/index.html")

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")
    

    # Get the state of the page right now.
    @app.get("/api/state")
    def state():
        token = request.cookies.get("team")
        team = store.get_team(token)
        if team is None:
            return jsonify({"error": "not_registered"}), 401
        
        progress = progression.summary(token)
        node = progression.current_node(token)
        distance = None

        if node is not None:
            reading = store.get_readings(node).get(team["mac"])
            distance = describe(reading)
        
        return jsonify({
            "team": team["name"], 
            "progress": progress,
            "node":node,
            "distance": distance,
        })

    return app


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    create_app().run(host="0.0.0.0", port = 8080, debug = debug)
