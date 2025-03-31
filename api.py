from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)
API_KEY = os.getenv("SCUM_API_KEY", "default_secret_key")

# Global variable that will store SCUM bot check-in information.
active_scum_bot = None

@app.route("/scum_checkin", methods=["POST"])
def scum_checkin():
    global active_scum_bot
    data = request.get_json()
    if not data or "callback_url" not in data:
        return jsonify({"error": "Missing callback_url"}), 400
    active_scum_bot = {
        "callback_url": data["callback_url"],
        "last_checkin": datetime.now().isoformat()
    }
    return jsonify({"status": "SCUM bot registered", "active_scum_bot": active_scum_bot}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
