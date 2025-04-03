from flask import Flask, jsonify, request, render_template, Blueprint
from datetime import datetime
import os
import requests
from functools import wraps

app = Flask(__name__)

API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

# In-memory bot registry; key is bot_id, value is a dict of details.
bots = {}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

# Create a blueprint so all API endpoints are under /api
api_bp = Blueprint('api', __name__)

@api_bp.route('/bot/register', methods=['POST'])
@require_api_key
def register_bot():
    data = request.json
    bot_id = data['bot_id']
    
    # Store registration details along with the timestamp
    bots[bot_id] = {
        'last_seen': datetime.now().isoformat(),
        'callback_url': data['callback_url'],
        'public_ip': data['public_ip'],
        'version': data.get("version", "unknown"),
        'status': 'online'
    }
    
    # Optionally send a Discord update
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
    
    if bot_id not in bots:
        return jsonify({"error": "Bot not found"}), 404
        
    try:
        # Forward the command to the bot's callback URL
        response = requests.post(
            bots[bot_id]['callback_url'],
            json=data['command'],
            headers={'X-API-Key': API_KEY},
            timeout=5
        )
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/bot/heartbeat', methods=['POST'])
@require_api_key
def receive_heartbeat():
    bot_id = request.json['bot_id']
    if bot_id in bots:
        bots[bot_id]['last_seen'] = datetime.now().isoformat()
    return jsonify({"status": "updated"})

@api_bp.route('/bot/feedback', methods=['POST'])
@require_api_key
def receive_feedback():
    data = request.json
    # Here you can log feedback from the bot after executing a command.
    print(f"Feedback received for bot {data.get('bot_id')}: {data}")
    return jsonify({"status": "feedback received"})

# A simple status page (for debugging) that shows all registered bots.
@app.route('/')
def status():
    return render_template('status.html', bots=bots)

# Register blueprint so that all API routes are prefixed with /api
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8079))
    app.run(host='0.0.0.0', port=port)
