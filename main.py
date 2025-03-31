from threading import Thread
from waitress import serve
from api import app as registration_app
from discord_bot import bot, BOT_TOKEN

def run_api_server():
    # Explicitly bind to 0.0.0.0
    serve(registration_app, host="0.0.0.0", port=8079, threads=4)

if __name__ == "__main__":
    # Use regular thread (not daemon)
    api_thread = Thread(target=run_api_server)
    api_thread.start()
    
    # Start Discord bot
    bot.run(BOT_TOKEN)
    
    # Keep the main thread alive
    api_thread.join()
