from threading import Thread
from waitress import serve
from app.vps_server import app, db
from app.discord_bot import bot
import os

def run_flask():
    with app.app_context():
        db.create_all()
    serve(app, host='0.0.0.0', port=int(os.getenv('PORT', 8079)))

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.run(os.getenv('DISCORD_TOKEN'))
