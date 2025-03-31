from threading import Thread
from flask import Flask
from discord_bot import bot, BOT_TOKEN

# Minimal Flask app for health checks.
app = Flask("health")

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # Start Flask in a separate thread.
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start the Discord bot.
    bot.run(BOT_TOKEN)
