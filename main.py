from threading import Thread
from waitress import serve
from app.vps_server import app, db  # Import the app and database instance
from app.discord_bot import bot
import os

def run_api_server():
    port = int(os.environ.get("PORT", 8079))
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    serve(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start the API server in a background thread.
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start the Discord bot (blocking call).
    bot.run(os.getenv('DISCORD_TOKEN'))
