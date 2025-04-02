import os
import uuid
import requests
import json
import logging
import time
from flask import Flask, request, jsonify
from threading import Thread
from state_manager import BotState, get_state
from bot_ready import send_verification_message, send_status_check_message, send_chat_message
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Use an environment variable for the port if available, default to 5001.
PORT = int(os.environ.get("PORT", 5001))

class AutoConfigBot:
    def __init__(self):
        self.config_file = "bot_config.json"
        self.config = self.load_or_create_config()
        # Print the bot_id for easy lookup.
        print(f"SCUM BOT ID: {self.config['bot_id']}")
        self.api_key = os.getenv("VPS_API_KEY")
        self.vps_url = os.getenv("VPS_API_URL")
        self.public_ip = self.get_public_ip()
        self.app = Flask(__name__)
        self.setup_routes()
        
    def load_or_create_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
            else:
                config = {
                    "bot_id": str(uuid.uuid4()),
                    "last_ip": ""
                }
                with open(self.config_file, "w") as f:
                    json.dump(config, f)
                return config
        except Exception as e:
            logging.error(f"Config error: {str(e)}")
            return {"bot_id": str(uuid.uuid4()), "last_ip": ""}
    
    def get_public_ip(self):
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            return response.json()["ip"]
        except:
            try:
                return requests.get("https://ipinfo.io/ip", timeout=5).text.strip()
            except:
                logging.error("Failed to detect public IP")
                return "unknown"
    
    def register_with_vps(self):
        # Note: The callback URL uses the port defined by PORT.
        callback_url = f"http://{self.public_ip}:{PORT}/api/command"
        payload = {
            "bot_id": self.config["bot_id"],
            "callback_url": callback_url,
            "public_ip": self.public_ip
        }
        try:
            response = requests.post(
                f"{self.vps_url}/register",
                json=payload,
                headers={"X-API-Key": self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                logging.info("Successfully registered with VPS")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Registration failed: {str(e)}")
            return False
    
    def setup_routes(self):
        # Health check route for container monitoring.
        @self.app.route("/", methods=["GET"])
        def health():
            return jsonify({"status": "ok"}), 200

        @self.app.route('/api/command', methods=['POST'])
        def handle_command():
            if request.headers.get("X-API-Key") != self.api_key:
                return jsonify({"error": "Unauthorized"}), 403

            if get_state() not in [BotState.BOT_READY, BotState.BOT_VERIFYING]:
                return jsonify({"error": "Bot not ready"}), 503

            command = request.json.get("command")
            try:
                if command == "verify":
                    result = send_verification_message(open_chat=False)
                elif command == "status":
                    result = send_status_check_message(open_chat=False)
                elif command.startswith("say "):
                    # New: extract the message and send it in-game.
                    msg = command[4:].strip()
                    result = send_chat_message(message=msg, open_chat=True)
                else:
                    return jsonify({"error": "Invalid command"}), 400

                self.send_feedback("command_success", {
                    "command": command,
                    "result": result
                })
                return jsonify({"status": "success"}), 200
            except Exception as e:
                logging.error(f"Command failed: {str(e)}")
                return jsonify({"error": "Execution failed"}), 500

    def send_feedback(self, event_type, data):
        try:
            requests.post(
                f"{self.vps_url}/feedback",
                json={
                    "bot_id": self.config["bot_id"],
                    "event": event_type,
                    "data": data,
                    "timestamp": int(time.time())
                },
                headers={"X-API-Key": self.api_key},
                timeout=5
            )
        except Exception as e:
            logging.error(f"Feedback failed: {str(e)}")
    
    def start(self):
        if not self.register_with_vps():
            logging.error("Initial registration failed")
            return

        Thread(
            target=lambda: self.app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False),
            daemon=True
        ).start()

        # Heartbeat thread to keep the VPS updated.
        def heartbeat_loop():
            while True:
                try:
                    requests.post(
                        f"{self.vps_url}/heartbeat",
                        json={"bot_id": self.config["bot_id"]},
                        headers={"X-API-Key": self.api_key},
                        timeout=5
                    )
                except Exception as e:
                    logging.error(f"Heartbeat failed: {str(e)}")
                time.sleep(60)

        Thread(target=heartbeat_loop, daemon=True).start()

# For testing purposes, instantiate and start the bot.
if __name__ == "__main__":
    bot_api = AutoConfigBot()
    bot_api.start()
    # Keep the main thread alive.
    while True:
        time.sleep(10)
