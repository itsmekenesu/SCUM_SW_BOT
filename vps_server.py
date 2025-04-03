from flask import Flask, jsonify, request, render_template
from datetime import datetime
import json
import os
import requests
from functools import wraps

app = Flask(__name__)
API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

# In-memory bot registry
bots = {}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def status():
    return render_template('status.html', bots=bots)

@app.route('/bot/register', methods=['POST'])
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
    
    # Send Discord notification
    requests.post(DISCORD_WEBHOOK, json={
        'content': f"🟢 Bot {bot_id} came online\nIP: {data['public_ip']}"
    })
    
    return jsonify({"status": "registered"})

@app.route('/bot/command', methods=['POST'])
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

@app.route('/bot/heartbeat', methods=['POST'])
@require_api_key
def receive_heartbeat():
    bot_id = request.json['bot_id']
    if bot_id in bots:
        bots[bot_id]['last_seen'] = datetime.now().isoformat()
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8079)
