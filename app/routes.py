from flask import jsonify, request
from .database import get_connection
import psutil
import datetime
import logging

logger = logging.getLogger(__name__)

def init_routes(app):
    @app.route('/api/health')
    def health_check():
        try:
            with get_connection() as conn:
                conn.execute("SELECT 1")
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy"}), 500

    @app.route('/api/bot/register', methods=['POST'])
    def register_bot():
        try:
            data = request.json
            with get_connection() as conn:
                conn.execute('''INSERT OR REPLACE INTO bots 
                             VALUES (?, ?, ?, ?, ?, ?)''',
                             (data['bot_id'], datetime.datetime.now().isoformat(),
                              data.get('callback_url'), data.get('public_ip'),
                              data.get('version', 'unknown'), 'online'))
                conn.commit()
            return jsonify({"status": "registered"})
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return jsonify({"error": "Registration failed"}), 500
