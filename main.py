"""
main.py

Main SCUM bot code that monitors SCUM logs, manages game state, and interacts with the local API.
It performs recovery screen identification, updates game state, fetches online players, and 
also starts a registration API server (using Waitress) so that a Discord bot can handle account linking.
"""

from threading import Thread
from flask import Flask
from discord_bot import bot, BOT_TOKEN

# Minimal Flask app for health checks.
app = Flask("health")

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    # Run on port 8079 to match DigitalOcean's readiness probe.
    app.run(host="0.0.0.0", port=8079)

if __name__ == "__main__":
    # Start Flask in a separate thread.
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start the Discord bot.
    bot.run(BOT_TOKEN)
