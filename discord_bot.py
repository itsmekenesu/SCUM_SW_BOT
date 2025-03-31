import os
import requests
import discord
from discord.ext import commands
from discord import ui

# Retrieve the bot token from environment variables.
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise Exception("DISCORD_TOKEN is not set in environment variables!")

SCUM_API_KEY = os.getenv("SCUM_API_KEY", "default_secret_key")

# Import the active_scum_bot variable from our API module.
from api import active_scum_bot

class ControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Send Text", style=discord.ButtonStyle.success, custom_id="send_text")
    async def send_text(self, interaction: discord.Interaction, button: ui.Button):
        # Re-import active_scum_bot to get the latest value.
        from api import active_scum_bot
        if not active_scum_bot:
            await interaction.response.send_message("SCUM bot is offline.", ephemeral=True)
            return

        callback_url = active_scum_bot.get("callback_url")
        payload = {"text": "Command triggered via Discord"}
        headers = {"X-API-Key": SCUM_API_KEY}
        try:
            response = requests.post(callback_url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                await interaction.response.send_message("Command forwarded to SCUM bot!", ephemeral=True)
            else:
                await interaction.response.send_message(f"SCUM bot error: {response.text}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error connecting to SCUM bot: {e}", ephemeral=True)

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel_id = int(os.getenv("REGISTRATION_CHANNEL_ID", "1355434230594666594"))
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("SCUM Bot Control Panel", view=ControlView())
    else:
        print("Channel for control panel not found.")

# Export BOT_TOKEN and bot for use in main.py
__all__ = ['bot', 'BOT_TOKEN']
