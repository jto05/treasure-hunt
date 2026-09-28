from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)
    
    # Treasure reports the average RSSI per phone MAC address to server
    # every few seconds
    @app.post("/api/report")
    def report():
        return jsonify()

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
