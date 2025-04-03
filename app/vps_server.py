from flask import Flask, jsonify, request, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
from functools import wraps

app = Flask(__name__)

# Configure SQLAlchemy to use SQLite local database file
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///bots.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

# Database model for bots
class Bot(db.Model):
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

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

# All API endpoints are grouped under this blueprint.
api_bp = Blueprint('api', __name__)

@api_bp.route('/bot/register', methods=['POST'])
@require_api_key
def register_bot():
    data = request.json
    bot_id = data['bot_id']
    now = datetime.now()

    # Upsert bot registration
    bot = Bot.query.get(bot_id)
    if not bot:
        bot = Bot(bot_id=bot_id)
    bot.last_seen = now
    bot.callback_url = data['callback_url']
    bot.public_ip = data['public_ip']
    bot.version = data.get("version", "unknown")
    bot.status = 'online'
    db.session.add(bot)
    db.session.commit()

    # Send a Discord update to the designated channel
    try:
        requests.post(DISCORD_WEBHOOK, json={
            'content': f"🟢 Bot {bot_id} registered (IP: {data['public_ip']})."
        })
    except Exception as e:
        print(f"Discord update failed: {e}")

    return jsonify({"status": "registered"})

@api_bp.route('/bot/command', methods=['POST'])
@require_api_key
def forward_command():
    data = request.json
    bot_id = data['bot_id']
    bot = Bot.query.get(bot_id)
    
    if not bot:
        return jsonify({"error": "Bot not found"}), 404
        
    try:
        response = requests.post(
            bot.callback_url,
            json=data['command'],
            headers={'X-API-Key': API_KEY},
            timeout=10  # Increased timeout for callback response
        )
        return response.json()
    except Exception as e:
        print(f"Error forwarding command to {bot.callback_url}: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/bot/heartbeat', methods=['POST'])
@require_api_key
def receive_heartbeat():
    bot_id = request.json['bot_id']
    bot = Bot.query.get(bot_id)
    if bot:
        bot.last_seen = datetime.now()
        db.session.commit()
    return jsonify({"status": "updated"})

@api_bp.route('/bot/feedback', methods=['POST'])
@require_api_key
def receive_feedback():
    data = request.json
    print(f"Feedback received for bot {data.get('bot_id')}: {data}")
    return jsonify({"status": "feedback received"})

@app.route('/')
def status():
    # Debugging page to display all registered bots
    bots = Bot.query.all()
    bots_list = [bot.as_dict() for bot in bots]
    return render_template('status.html', bots=bots_list)

app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 8079))
    app.run(host='0.0.0.0', port=port)
