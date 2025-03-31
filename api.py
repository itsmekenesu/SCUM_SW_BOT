from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from datetime import datetime

app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)
API_KEY = os.getenv("VPS_API_KEY")
bots = {}  # {bot_id: {"callback_url": "", "last_seen": ""}}

@app.route("/bot/register", methods=["POST"])
@limiter.limit("5/minute")
def register_bot():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403

    data = request.json
    bot_id = data.get("bot_id")
    callback_url = data.get("callback_url")

    if not bot_id or not callback_url:
        return jsonify({"error": "Missing parameters"}), 400

    bots[bot_id] = {
        "callback_url": callback_url,
        "last_seen": datetime.utcnow().isoformat()
    }
    return jsonify({"status": "Registered", "bot_id": bot_id}), 200

@app.route("/bot/command", methods=["POST"])
@limiter.limit("20/minute")
def send_command():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403

    data = request.json
    bot_id = data.get("bot_id")
    command = data.get("command")

    if not bot_id or not command:
        return jsonify({"error": "Missing parameters"}), 400

    bot = bots.get(bot_id)
    if not bot:
        return jsonify({"error": "Bot not found"}), 404

    try:
        response = requests.post(
            bot["callback_url"],
            json={"command": command},
            timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
