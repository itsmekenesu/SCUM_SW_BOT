# main.py - Combined entry point for local development
from threading import Thread
from waitress import serve
from app.vps_server import app, db  # Make sure you have app/__init__.py
from app.discord_bot import bot
import os

def run_flask_server():
    """Run Flask API server using Waitress"""
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8079)))

if __name__ == "__main__":
    # Start Flask server in a daemon thread
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    # Start Discord bot in main thread (blocking)
    bot.run(os.getenv('DISCORD_TOKEN'))
