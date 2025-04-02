import threading
import time
import logging
import os
from dotenv import load_dotenv
from waitress import serve

load_dotenv()
logging.basicConfig(level=logging.INFO)
PORT = int(os.getenv("PORT", 8079))

# Import the SCUM BOT Flask app and class.
from scum_bot import app as scum_app, ScumBot
# Import the Discord bot runner.
from discord_bot import run_discord_bot

def run_scum_bot_server():
    bot = ScumBot()
    bot.start()
    logging.info(f"Starting SCUM BOT server on port {PORT}")
    serve(scum_app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # Start the SCUM BOT server in a daemon thread.
    scum_thread = threading.Thread(target=run_scum_bot_server, daemon=True)
    scum_thread.start()
    # Wait briefly for the SCUM BOT server to start.
    time.sleep(5)
    # Start the Discord bot (this call blocks).
    run_discord_bot()
