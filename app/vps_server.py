import os
import logging
import sqlite3
import threading
import asyncio
from datetime import datetime
from flask import Flask, jsonify, request
import discord
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

# Database configuration
DATABASE_PATH = '/tmp/bots.db'

def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS bots
                        (bot_id TEXT PRIMARY KEY,
                         last_seen TIMESTAMP,
                         callback_url TEXT,
                         public_ip TEXT,
                         version TEXT,
                         status TEXT)''')
        conn.commit()

init_db()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class DiscordBotThread(threading.Thread):
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot.start(os.getenv('DISCORD_TOKEN')))
        except Exception as e:
            logger.error(f"Discord bot failed: {str(e)}")
        finally:
            loop.close()

# Start Discord bot in background thread
DiscordBotThread(daemon=True).start()

@app.route('/api/health')
def health_check():
    try:
        mem = psutil.virtual_memory()
        return jsonify({
            "status": "healthy",
            "memory_used": f"{mem.percent}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy"}), 500

@app.route('/api/bot/register', methods=['POST'])
def register_bot():
    try:
        data = request.json
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute('''INSERT OR REPLACE INTO bots 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                         (data['bot_id'], datetime.now().isoformat(),
                          data.get('callback_url'), data.get('public_ip'),
                          data.get('version', 'unknown'), 'online'))
            conn.commit()
        
        return jsonify({"status": "registered"})
    
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"Command sync error: {str(e)}")

@bot.tree.command(name="status", description="Check bot status")
async def status(interaction: discord.Interaction):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM bots")
            count = cur.fetchone()[0]
        
        mem = psutil.virtual_memory()
        await interaction.response.send_message(
            f"🟢 System Status\n"
            f"- Registered Bots: {count}\n"
            f"- Memory Used: {mem.percent}%\n"
            f"- Last Check: {datetime.now().isoformat()}"
        )
    except Exception as e:
        logger.error(f"Status command failed: {str(e)}")
        await interaction.response.send_message("❌ Error checking status")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8079))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
