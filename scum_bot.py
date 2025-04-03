import os
import logging
import sqlite3
import threading
import asyncio
from datetime import datetime
from flask import Flask, jsonify, request
import discord
from discord import app_commands
from discord.ext import commands
import requests
import psutil
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # NEW: For retry logic [[5]][[6]]

# =======================
# CONFIGURATION
# =======================
API_KEY = os.getenv('VPS_API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AUTHORIZED_USER_ID = 912964118447816735
DATABASE_PATH = '/tmp/bots.db'

# =======================
# LOGGING SETUP
# =======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
# NEW: Suppress urllib3 debug logs from requests [[9]]
logging.getLogger('urllib3').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# =======================
# FLASK APPLICATION
# =======================
app = Flask(__name__)

# =======================
# DATABASE SETUP
# =======================
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS bots
                        (bot_id TEXT PRIMARY KEY,
                         last_seen TIMESTAMP,
                         callback_url TEXT,
                         public_ip TEXT,
                         version TEXT,
                         status TEXT)''')
        conn.commit()
    finally:
        conn.close()

init_db()

# =======================
# DISCORD BOT SETUP
# =======================
intents = discord.Intents.default()
intents.message_content = True

class ScumBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
    async def setup_hook(self):
        await self.tree.sync()

bot = ScumBot()

# =======================
# CORE FUNCTIONALITY
# =======================
def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

def process_command(bot_id: str, command: str, user: str):
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT callback_url FROM bots WHERE bot_id = ?",
                (bot_id,)
            )
            result = cur.fetchone()
            
        if not result:
            return False, "Bot not registered"
            
        callback_url = result[0]

        # NEW: Add retry logic with session [[5]][[6]][[7]]
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)

        response = http.post(
            callback_url,
            json={
                "command": command,
                "source": "discord",
                "user": user
            },
            headers={"X-API-Key": API_KEY},
            timeout=15  # Increased timeout for reliability
        )
        
        # NEW: Validate response format [[3]][[4]]
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}: {response.reason}"
            
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return False, f"Unexpected response format: {response.text}"
            
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            return False, f"Invalid JSON response: {response.text}"  # [[4]][[6]]
            
        if 'error' in response_data:
            return False, response_data['error']
            
        return True, response_data.get('result', 'Command executed')
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during command processing: {str(e)}")
        return False, f"Network error: {str(e)}"
    except Exception as e:
        logger.error(f"Command processing failed: {str(e)}", exc_info=True)
        return False, f"Internal error: {str(e)}"

# =======================
# FLASK ROUTES
# =======================
@app.route('/api/health')
def health_check():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "memory": f"{psutil.virtual_memory().percent}%"
        })
    except Exception as e:
        return jsonify({"status": "unhealthy"}), 500

@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    try:
        data = request.get_json()  # NEW: Use built-in Flask method [[8]]
        with get_db_connection() as conn:
            conn.execute('''INSERT OR REPLACE INTO bots 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                         (data['bot_id'], datetime.now().isoformat(),
                          data.get('callback_url'), data.get('public_ip'),
                          data.get('version', 'unknown'), 'online'))
            conn.commit()
        return jsonify({"status": "registered"})
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

# =======================
# DISCORD COMMANDS
# =======================
@bot.tree.command(name="scum", description="Manage SCUM bots")
@app_commands.describe(
    bot_id="Target bot ID", 
    command="Command (verify/status/say <message>)"
)
async def scum_command(interaction: discord.Interaction, bot_id: str, command: str):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    success, result = process_command(bot_id, command, str(interaction.user))
    
    if success:
        await interaction.followup.send(f"✅ {result}")
    else:
        await interaction.followup.send(f"❌ Error: {result}")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

# =======================
# APPLICATION STARTUP
# =======================
def run_flask():
    port = int(os.getenv('PORT', 8079))
    app.run(host='0.0.0.0', port=port)

def run_discord():
    bot.run(DISCORD_TOKEN)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    run_discord()
