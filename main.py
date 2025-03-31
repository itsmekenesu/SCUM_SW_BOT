from threading import Thread
from waitress import serve
from api import app as api_app
from discord_bot import bot, BOT_TOKEN

def run_api():
    print("🌐 Starting API server on 0.0.0.0:8079")
    serve(api_app, host="0.0.0.0", port=8079)
    print("✅ API Server Ready")

if __name__ == "__main__":
    # Start API first
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Then start Discord bot
    print("🤖 Starting Discord bot...")
    bot.run(BOT_TOKEN)
    
    # Keep main thread alive
    while True:
        pass
