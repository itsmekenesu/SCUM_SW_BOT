import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import requests

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URI', 
    'sqlite:////workspace/.data/bots.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300
}

db = SQLAlchemy(app)

class Bot(db.Model):
    __tablename__ = 'bots'
    bot_id = db.Column(db.String(50), primary_key=True)
    last_seen = db.Column(db.DateTime)
    callback_url = db.Column(db.String(255))
    public_ip = db.Column(db.String(50))
    version = db.Column(db.String(50), default="unknown")
    status = db.Column(db.String(20), default="online")

    def as_dict(self):
        return {
            "bot_id": self.bot_id,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "callback_url": self.callback_url,
            "public_ip": self.public_ip,
            "version": self.version,
            "status": self.status
        }

# Initialize database
def initialize_database():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized successfully at: %s", 
                      app.config['SQLALCHEMY_DATABASE_URI'])
            # Verify database connection
            db.session.execute('SELECT 1').fetchone()
            logger.info("Database connection test successful")
        except SQLAlchemyError as e:
            logger.critical("Database initialization failed: %s", str(e))
            sys.exit(1)

initialize_database()

@app.before_request
def log_request_info():
    logger.info("Request: %s %s", request.method, request.path)

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Simple database check
        db.session.execute('SELECT 1').fetchone()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        })
    except SQLAlchemyError:
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500

@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    try:
        data = request.get_json()
        if not data or 'bot_id' not in data:
            return jsonify({"error": "Invalid request"}), 400

        bot = Bot.query.get(data['bot_id']) or Bot(bot_id=data['bot_id'])
        
        update_fields = {
            'last_seen': datetime.utcnow(),
            'callback_url': data.get('callback_url'),
            'public_ip': data.get('public_ip'),
            'version': data.get('version', 'unknown'),
            'status': 'online'
        }

        for key, value in update_fields.items():
            if value is not None:
                setattr(bot, key, value)

        db.session.add(bot)
        db.session.commit()

        # Send Discord notification
        if webhook := os.getenv('DISCORD_WEBHOOK'):
            try:
                requests.post(
                    webhook,
                    json={'content': f"🟢 Bot {data['bot_id']} registered"},
                    timeout=3
                )
            except Exception as e:
                logger.warning("Discord notification failed: %s", str(e))

        return jsonify(bot.as_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error during registration: %s", str(e))
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/bot/heartbeat', methods=['POST'])
def receive_heartbeat():
    try:
        data = request.get_json()
        if not data or 'bot_id' not in data:
            return jsonify({"error": "Invalid request"}), 400

        bot = Bot.query.get(data['bot_id'])
        if not bot:
            return jsonify({"error": "Bot not found"}), 404

        bot.last_seen = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "updated"})

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Database error in heartbeat: %s", str(e))
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8079))
    logger.info("Starting application on port %d", port)
    app.run(host='0.0.0.0', port=port)
