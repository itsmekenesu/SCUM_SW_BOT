from flask import Flask, request, jsonify
from flask_limiter import Limiter
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)
limiter = Limiter(app, key_func=lambda: request.headers.get("X-Bot-ID", "default"))
bots = {}

@app.route('/register', methods=['POST'])
@limiter.limit("5/minute")
def register_bot():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("VPS_API_KEY"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    bot_id = data["bot_id"]
    
    bots[bot_id] = {
        "callback_url": data["callback_url"],
        "public_ip": data["public_ip"],
        "last_seen": datetime.utcnow(),
        "status": "online"
    }
    
    return jsonify({
        "status": "registered",
        "bot_id": bot_id
    }), 200

@app.route('/heartbeat', methods=['POST'])
@limiter.limit("10/minute")
def heartbeat():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("VPS_API_KEY"):
        return jsonify({"error": "Unauthorized"}), 403

    bot_id = request.json["bot_id"]
    if bot_id in bots:
        bots[bot_id]["last_seen"] = datetime.utcnow()
        bots[bot_id]["status"] = "online"
    return jsonify({"status": "updated"}), 200

@app.route('/feedback', methods=['POST'])
@limiter.limit("20/minute")
def handle_feedback():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("VPS_API_KEY"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    # Process feedback here (e.g., send to Discord)
    print(f"Received feedback: {data}")
    return jsonify({"status": "received"}), 200

@app.route('/send_command', methods=['POST'])
def send_command():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("VPS_API_KEY"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    bot_id = data["bot_id"]
    command = data["command"]
    
    bot = bots.get(bot_id)
    if not bot:
        return jsonify({"error": "Bot not found"}), 404
        
    try:
        response = requests.post(
            bot["callback_url"],
            json={"command": command},
            headers={"X-API-Key": os.getenv("VPS_API_KEY")},
            timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
