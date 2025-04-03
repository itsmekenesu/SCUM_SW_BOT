import discord
from discord import app_commands
from discord.ext import commands
import os
import threading
import asyncio
from .database import get_connection
import requests
import logging

logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('VPS_API_KEY')
AUTHORIZED_USER_ID = 912964118447816735
NOTIFICATION_CHANNEL_ID = 1355434230594666594

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.notification_channel = None
        
    async def setup_hook(self):
        await self.tree.sync()
        self.notification_channel = self.get_channel(NOTIFICATION_CHANNEL_ID)

bot = DiscordBot()

async def send_notification(message: str):
    if bot.notification_channel:
        await bot.notification_channel.send(f"🔔 {message}")

def process_scum_command(user: discord.User, bot_id: str, command: str) -> (bool, str):
    try:
        with get_connection() as conn:
            cur = conn.execute("SELECT callback_url FROM bots WHERE bot_id = ?", (bot_id,))
            result = cur.fetchone()
            
        if not result:
            return False, "❌ Bot not registered"
            
        response = requests.post(
            result[0],
            json={"command": command, "user": str(user)},
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            asyncio.run_coroutine_threadsafe(
                send_notification(f"Command to {bot_id} by {user}"),
                bot.loop
            )
            return True, "✅ Command executed"
        return False, f"❌ Error: {response.json().get('error', 'Unknown')}"
        
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        return False, f"🚨 System error: {str(e)}"

@bot.tree.command(name="scum", description="Manage SCUM bots")
@app_commands.describe(bot_id="Bot ID", command="Command (verify/status/say)")
async def scum_command(interaction: discord.Interaction, bot_id: str, command: str):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        return
    
    await interaction.response.defer()
    success, msg = process_scum_command(interaction.user, bot_id, command)
    await interaction.followup.send(msg)

def run_bot():
    bot.run(os.getenv('DISCORD_TOKEN'))
