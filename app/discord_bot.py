import discord
from discord import app_commands
from discord.ext import commands
import os
import requests

API_URL = os.getenv('VPS_API_URL')
API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
AUTHORIZED_USER_ID = 912964118447816735  # Only allow this Discord user

def send_update(message: str):
    try:
        requests.post(DISCORD_WEBHOOK, json={'content': message}, timeout=5)
    except Exception as e:
        print(f"Failed to send update to webhook: {e}")

class ScumBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()

bot = ScumBot()

@bot.tree.command(name="scum", description="Manage SCUM bots")
@app_commands.describe(bot_id="Target bot ID", command="Command to send")
async def scum_command(interaction: discord.Interaction, bot_id: str, command: str):
    # Enforce that only the authorized Discord account can use this command.
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message(
            "❌ You are not authorized to use this command.",
            ephemeral=True
        )
        send_update(f"Unauthorized command attempt by {interaction.user} (ID: {interaction.user.id}).")
        return
    
    try:
        response = requests.post(
            f"{API_URL}/bot/command",
            json={
                "bot_id": bot_id,
                "command": {
                    "type": "discord_command",
                    "content": command,
                    "user": str(interaction.user)
                }
            },
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            await interaction.response.send_message(
                f"✅ Command sent to bot {bot_id}",
                ephemeral=True
            )
            send_update(f"Command sent to bot {bot_id} by {interaction.user}.")
        else:
            error_msg = response.json().get('error', 'Unknown error')
            await interaction.response.send_message(
                f"❌ Error: {error_msg}",
                ephemeral=True
            )
            send_update(f"Error sending command to bot {bot_id} by {interaction.user}: {error_msg}")
            
    except Exception as e:
        await interaction.response.send_message(
            f"🚨 Connection failed: {str(e)}",
            ephemeral=True
        )
        send_update(f"Connection failed when sending command by {interaction.user}: {str(e)}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
