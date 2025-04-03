from flask import Flask, jsonify, request, render_template, Blueprint
from datetime import datetime
import os
import requests
from functools import wraps

app = Flask(__name__)

API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

# Create a blueprint for API routes
api_bp = Blueprint('api', __name__)

# In-memory bot registry
bots = {}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/bot/register', methods=['POST'])
@require_api_key
def register_bot():
    data = request.json
    bot_id = data['bot_id']
    
    bots[bot_id] = {
        'last_seen': datetime.now().isoformat(),
        'callback_url': data['callback_url'],
        'public_ip': data['public_ip'],
        'status': 'online'
    }
    
    # Send Discord notification about bot registration
    requests.post(DISCORD_WEBHOOK, json={
        'content': f"🟢 Bot {bot_id} came online\nIP: {data['public_ip']}"
    })
    
    return jsonify({"status": "registered"})

@api_bp.route('/bot/command', methods=['POST'])
@require_api_key
def forward_command():
    data = request.json
    bot_id = data['bot_id']
    
    if bot_id not in bots:
        return jsonify({"error": "Bot not found"}), 404
        
    try:
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

# Register blueprint so that routes are accessible under /api
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def status():
    # This page shows a simple status of registered bots.
    return render_template('status.html', bots=bots)

# Placeholder for the AutoConfigBot class used in main.py
class AutoConfigBot:
    def start(self):
        print("AutoConfigBot started")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8079))
    app.run(host='0.0.0.0', port=port)
