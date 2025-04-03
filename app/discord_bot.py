import discord
from discord import app_commands
from discord.ext import commands
import os
import requests

API_URL = os.getenv('VPS_API_URL')
API_KEY = os.getenv('VPS_API_KEY')

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
    # Verify admin role
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "❌ Administrator permission required",
            ephemeral=True
        )
    
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
        else:
            await interaction.response.send_message(
                f"❌ Error: {response.json()['error']}",
                ephemeral=True
            )
            
    except Exception as e:
        await interaction.response.send_message(
            f"🚨 Connection failed: {str(e)}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
