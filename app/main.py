from flask import Flask
from .routes import init_routes
from .discord_bot import run_bot
import threading
import logging

def create_app():
    app = Flask(__name__)
    init_routes(app)
    return app

def run_flask():
    app = create_app()
    port = int(os.getenv('PORT', 8079))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Initialize database
    from .database import init_db
    init_db()
    
    # Start Flask in thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Discord bot
    run_bot()
