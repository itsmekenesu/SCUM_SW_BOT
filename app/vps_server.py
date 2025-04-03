import os
import sys
import logging
import traceback
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import psutil

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'SQLALCHEMY_DATABASE_URI', 
    'sqlite:////tmp/bots.db'
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
try:
    with app.app_context():
        db.create_all()
        logger.info("Database initialized at: %s", app.config['SQLALCHEMY_DATABASE_URI'])
        db.session.execute(text('PRAGMA journal_mode=WAL'))
        db.session.commit()
except Exception as e:
    logger.critical("Database initialization failed: %s", traceback.format_exc())
    sys.exit(1)

@app.route('/api/health')
def health_check():
    try:
        # Check database connection
        db.session.execute(text('SELECT 1')).fetchone()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "memory": psutil.virtual_memory().percent,
            "cpu": psutil.cpu_percent()
        })
    except Exception as e:
        logger.error("Health check failed: %s", traceback.format_exc())
        return jsonify({"status": "unhealthy"}), 500

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

        return jsonify(bot.as_dict())

    except Exception as e:
        db.session.rollback()
        logger.error("Registration error: %s", traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def status_dashboard():
    try:
        bots = Bot.query.all()
        return render_template('status.html', bots=[b.as_dict() for b in bots])
    except Exception as e:
        logger.error("Dashboard error: %s", traceback.format_exc())
        return render_template('error.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8079))
    logger.info("Starting server on port %d", port)
    app.run(host='0.0.0.0', port=port)
