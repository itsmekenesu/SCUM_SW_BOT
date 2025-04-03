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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
API_URL = os.getenv('VPS_API_URL')
API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
AUTHORIZED_USER_ID = 912964118447816735  # Replace with your user ID

# Database setup
DATABASE_PATH = '/tmp/bots.db'
conn_pool = sqlite3.connect(DATABASE_PATH, check_same_thread=False)

def init_db():
    with conn_pool:
        conn_pool.execute('''CREATE TABLE IF NOT EXISTS bots
                            (bot_id TEXT PRIMARY KEY,
                             last_seen TIMESTAMP,
                             callback_url TEXT,
                             public_ip TEXT,
                             version TEXT,
                             status TEXT)''')

init_db()

# Discord bot setup
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

def send_update(message: str):
    try:
        requests.post(DISCORD_WEBHOOK, json={'content': message}, timeout=5)
    except Exception as e:
        logger.error(f"Webhook failed: {str(e)}")

def process_scum_command(user: discord.User, bot_id: str, command: str) -> (bool, str):
    try:
        # Get bot callback URL from database
        with conn_pool:
            cur = conn_pool.execute(
                "SELECT callback_url FROM bots WHERE bot_id = ?",
                (bot_id,)
            )
            result = cur.fetchone()
        
        if not result:
            return False, "❌ Bot not registered"
            
        callback_url = result[0]
        
        # Forward command to bot
        response = requests.post(
            callback_url,
            json={
                "command": command,
                "source": "discord",
                "user": str(user)
            },
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            send_update(f"Command sent to {bot_id} by {user}")
            return True, f"✅ Command executed: {response.json().get('result', 'Success')}"
        else:
            error_msg = response.json().get('error', 'Unknown error')
            send_update(f"Error sending to {bot_id}: {error_msg}")
            return False, f"❌ Bot error: {error_msg}"
            
    except Exception as e:
        send_update(f"Connection failed: {str(e)}")
        return False, f"🚨 System error: {str(e)}"

# Discord commands implementation
@bot.tree.command(name="scum", description="Manage SCUM bots")
@app_commands.describe(
    bot_id="Target bot ID", 
    command="Command (verify/status/say <message>)"
)
async def scum_slash(interaction: discord.Interaction, bot_id: str, command: str):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        send_update(f"Unauthorized attempt by {interaction.user}")
        return

    await interaction.response.defer(ephemeral=True)
    success, msg = process_scum_command(interaction.user, bot_id, command)
    await interaction.followup.send(msg, ephemeral=True)

@bot.command(name="scum")
async def scum_text(ctx, bot_id: str, *, command: str):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("❌ Unauthorized", delete_after=10)
        send_update(f"Unauthorized attempt by {ctx.author}")
        return
        
    success, msg = process_scum_command(ctx.author, bot_id, command)
    await ctx.send(msg, delete_after=10)

# Help commands
@bot.tree.command(name="help", description="Show help")
async def help_slash(interaction: discord.Interaction):
    help_text = (
        "**SCUM Bot Commands**\n"
        "• `/scum bot_id:<id> command:verify` - Verify bot identity\n"
        "• `/scum bot_id:<id> command:status` - Get bot status report\n"
        "• `/scum bot_id:<id> command:say <message>` - Make bot send chat message\n"
        "Text commands: `!scum <bot_id> <command>`"
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    send_update(f"✅ Bot connected as {bot.user}")

# Core VPS functionality
@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    try:
        data = request.json
        with conn_pool:
            conn_pool.execute('''INSERT OR REPLACE INTO bots 
                               VALUES (?, ?, ?, ?, ?, ?)''',
                               (data['bot_id'], datetime.now().isoformat(),
                                data.get('callback_url'), data.get('public_ip'),
                                data.get('version', 'unknown'), 'online'))
        
        send_update(f"🟢 Bot {data['bot_id']} registered")
        return jsonify({"status": "registered"})
    
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/bot/command', methods=['POST'])
def handle_bot_command():
    try:
        data = request.json
        command = data['command']['content']
        bot_id = data['bot_id']
        
        # Add your custom command handling logic here
        if command.startswith("verify"):
            return jsonify({"result": "Verification successful"})
        elif command.startswith("status"):
            return jsonify({"status": "online", "last_seen": datetime.now().isoformat()})
        elif command.startswith("say"):
            message = command[3:].strip()
            return jsonify({"result": f"Message sent: {message}"})
            
        return jsonify({"error": "Unknown command"}), 400
        
    except Exception as e:
        logger.error(f"Command handling failed: {str(e)}")
        return jsonify({"error": "Command processing failed"}), 500

# System monitoring
@app.route('/api/health')
def health_check():
    try:
        mem = psutil.virtual_memory()
        with conn_pool:
            conn_pool.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "memory_used": f"{mem.percent}%",
            "timestamp": datetime.utcnow().isoformat(),
            "connected_bots": len(get_connected_bots())
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy"}), 500

def get_connected_bots():
    with conn_pool:
        cur = conn_pool.execute("SELECT bot_id FROM bots WHERE status = 'online'")
        return [row[0] for row in cur.fetchall()]

# Discord bot thread
def run_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.start(os.getenv('DISCORD_TOKEN')))
    except Exception as e:
        logger.error(f"Discord bot failed: {str(e)}")
    finally:
        loop.close()

threading.Thread(target=run_discord_bot, daemon=True).start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8079))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
