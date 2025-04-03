from threading import Thread
from waitress import serve
from api import app, AutoConfigBot
from discord_bot import bot
import os

def run_api_server():
    # Use the PORT environment variable (default to 8079)
    port = int(os.environ.get("PORT", 8079))
    serve(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Instantiate and start the AutoConfigBot (for setting up routes, registration, heartbeat, etc.)
    bot_api = AutoConfigBot()
    bot_api.start()

    # Start the API server in a background thread.
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start the Discord bot (this call is blocking).
    bot.run(os.getenv('DISCORD_TOKEN'))
