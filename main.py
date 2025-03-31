from threading import Thread
from waitress import serve
from api import app as registration_app
from discord_bot import bot, BOT_TOKEN

def run_api_server():
    # Serve the API (including /scum_checkin) on port 8079.
    serve(registration_app, host="0.0.0.0", port=8079)

if __name__ == "__main__":
    # Start the API server in a background thread.
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start the Discord bot.
    bot.run(BOT_TOKEN)
