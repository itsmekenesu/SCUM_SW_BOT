# vps_server.py
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import logging
import sys
import requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URI', 
    'sqlite:////workspace/.data/bots.db'  # DigitalOcean persistent storage
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database model
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

# Create tables (for initial setup)
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

# Middleware
@app.before_request
def log_request_info():
    logger.info(f"{request.method} {request.path} - Headers: {dict(request.headers)}")

# Helper functions
def get_auth_header():
    api_key = os.getenv('VPS_API_KEY')
    if not api_key:
        logger.error("VPS_API_KEY environment variable not set!")
        raise ValueError("API key not configured")
    return {'X-API-Key': api_key}

# Routes
@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        bot_id = data.get('bot_id')
        if not bot_id:
            return jsonify({"error": "Missing bot_id"}), 400

        bot = Bot.query.get(bot_id)
        if not bot:
            bot = Bot(bot_id=bot_id)
            db.session.add(bot)
            logger.info(f"New bot registered: {bot_id}")

        update_fields = {
            'last_seen': datetime.utcnow(),
            'callback_url': data.get('callback_url'),
            'public_ip': data.get('public_ip'),
            'version': data.get('version', 'unknown'),
            'status': 'online'
        }

        for key, value in update_fields.items():
            setattr(bot, key, value)

        db.session.commit()

        # Send Discord notification
        discord_webhook = os.getenv('DISCORD_WEBHOOK')
        if discord_webhook:
            try:
                requests.post(
                    discord_webhook,
                    json={'content': f"🟢 Bot {bot_id} registered (IP: {data['public_ip']})"},
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Discord notification failed: {str(e)}")

        return jsonify(bot.as_dict())

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/bot/heartbeat', methods=['POST'])
def receive_heartbeat():
    try:
        data = request.get_json()
        bot_id = data.get('bot_id')
        if not bot_id:
            return jsonify({"error": "Missing bot_id"}), 400

        bot = Bot.query.get(bot_id)
        if not bot:
            return jsonify({"error": "Bot not found"}), 404

        bot.last_seen = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "updated"})

    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def status_dashboard():
    try:
        bots = Bot.query.all()
        return render_template('status.html', bots=[b.as_dict() for b in bots])
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return render_template('error.html'), 500

# Database connection check
@app.route('/api/db-check')
def db_check():
    try:
        Bot.query.limit(1).all()
        return jsonify({"database": "connected"})
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return jsonify({"database": "connection failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8079))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', False))
