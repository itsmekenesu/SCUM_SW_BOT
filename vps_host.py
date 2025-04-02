import os
import time
import logging
from flask import Flask, request, jsonify
from threading import Thread

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# In-memory registry for online SCUM BOTs.
registered_bots = {}  # bot_id -> { "callback_url": str, "public_ip": str, "last_heartbeat": float }

@app.route('/register', methods=['POST'])
def register_bot():
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("VPS_API_KEY")
    if api_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    bot_id = data.get("bot_id")
    callback_url = data.get("callback_url")
    public_ip = data.get("public_ip")
    if not bot_id or not callback_url:
        return jsonify({"error": "Missing bot_id or callback_url"}), 400

    registered_bots[bot_id] = {
        "callback_url": callback_url,
        "public_ip": public_ip,
        "last_heartbeat": time.time()
    }
    logging.info(f"Registered bot {bot_id} with callback URL: {callback_url}")
    return jsonify({"status": "registered"}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("VPS_API_KEY")
    if api_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    bot_id = data.get("bot_id")
    if bot_id in registered_bots:
        registered_bots[bot_id]["last_heartbeat"] = time.time()
        logging.info(f"Heartbeat received from bot {bot_id}")
        return jsonify({"status": "heartbeat received"}), 200
    return jsonify({"error": "bot not registered"}), 404

@app.route('/feedback', methods=['POST'])
def feedback():
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("VPS_API_KEY")
    if api_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    bot_id = data.get("bot_id")
    event = data.get("event")
    feedback_data = data.get("data")
    timestamp = data.get("timestamp")
    logging.info(f"Feedback from bot {bot_id}: event={event}, data={feedback_data}, ts={timestamp}")
    return jsonify({"status": "feedback received"}), 200

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.get_json()
    command = data.get("command")
    if not command:
        return jsonify({"error": "Missing command"}), 400

    now = time.time()
    # Consider bots with a heartbeat in the last 2 minutes as online.
    online_bots = {bot_id: info for bot_id, info in registered_bots.items() if now - info["last_heartbeat"] < 120}
    if not online_bots:
        return jsonify({"error": "No bots online"}), 404

    # For simplicity, pick the first online bot.
    bot_id, bot_info = next(iter(online_bots.items()))
    callback_url = bot_info["callback_url"]

    try:
        import requests
        resp = requests.post(
            callback_url,
            json={"command": command},
            headers={"X-API-Key": os.getenv("VPS_API_KEY")},
            timeout=10
        )
        resp.raise_for_status()
        bot_response = resp.json()
    except Exception as e:
        logging.error(f"Failed to forward command to bot {bot_id}: {str(e)}")
        return jsonify({"error": f"Failed to forward command: {str(e)}"}), 500

    logging.info(f"Command forwarded to bot {bot_id}: {command}")
    return jsonify({"status": "command sent", "bot_id": bot_id, "bot_response": bot_response}), 200

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

def cleanup_bots():
    while True:
        now = time.time()
        stale = [bot_id for bot_id, info in registered_bots.items() if now - info["last_heartbeat"] > 300]
        for bot_id in stale:
            logging.info(f"Removing stale bot {bot_id}")
            del registered_bots[bot_id]
        time.sleep(60)

def run_vps_host():
    port = int(os.getenv("PORT", 5001))
    logging.info(f"Starting VPS host API server on port {port}")
    Thread(target=cleanup_bots, daemon=True).start()
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_vps_host()
