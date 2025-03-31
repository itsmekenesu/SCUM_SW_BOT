from threading import Thread
from waitress import serve
from api import app as registration_app
from discord_bot import bot, BOT_TOKEN
import time

def run_api_server():
    print("🔧 Starting API server on port 8079")
    serve(registration_app, host="0.0.0.0", port=8079, threads=4)
    print("✅ API server is running")

if __name__ == "__main__":
    print("🚀 Launching application...")
    
    # Start API server
    api_thread = Thread(target=run_api_server)
    api_thread.daemon = True
    api_thread.start()
    
    # Wait for API to initialize
    time.sleep(2)
    
    print("🤖 Starting Discord bot...")
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"❌ Bot failed: {str(e)}")
    
    # Keep main thread alive
    while True:
        time.sleep(1)
