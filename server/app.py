from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)
    
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
    # readings is keyed by phone MAC address (lowercase); rssi is the
    # ESP32's averaged dBm, n is packets heard in the last second, and
    # age_ms is how long ago that MAC was last heard. Only MACs heard in
    # the last 5s should be included.
    @app.post("/api/report")
    def report():
        data = request.get_json()
        if not data:
            return jsonify({"error": "bad_json"}), 400

        # TODO: implement in-memory storage

        # printing for testing
        print("Data:", data)

        return jsonify({"ok": True})


    # Register a team
    @app.post("/api/team")
    def register_team():
        return jsonify()

    # Get the state of the page right now.
    @app.get("/api/state")
    def state():
        return jsonify()

    # Get the description of minigame at specific node
    @app.get("/api/challenge/{node}")
    def get_challenge():
        return jsonify()

    # Start challenge at specific node
    @app.post("/api/challenge/{node}/start")
    def start_challenge():
        return jsonify()

    # Get leaderboard
    @app.get("/api/leaderboard")
    def leaderboard():
        return jsonify()

    # TODO: admin endpoints? lowk don't know if its needed

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port = 8080, debug = True)
