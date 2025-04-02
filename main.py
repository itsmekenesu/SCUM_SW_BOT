from threading import Thread
from waitress import serve
from api import app as registration_app
import discord_bot

def run_api_server():
    # Serve the API on port 8079.
    serve(registration_app, host="0.0.0.0", port=8079)

def run_discord_bot():
    discord_bot.run_bot()

if __name__ == "__main__":
    # Start the API server in a background thread.
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start the Discord bot in the main thread.
    run_discord_bot()
