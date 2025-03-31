import os
import sys
import logging
import discord
from discord.ext import commands
from discord import ui
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# Retrieve environment variables
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    logging.error("DISCORD_TOKEN is not set in environment variables.")
    sys.exit(1)

API_KEY = os.getenv("SCUM_API_KEY", "default_secret_key")
SCUM_API_URL = os.getenv("SCUM_API_URL", "http://localhost:5000")

try:
    REGISTRATION_CHANNEL_ID = int(os.getenv("REGISTRATION_CHANNEL_ID", "1355434230594666594"))
    CONTROL_CHANNEL_ID = int(os.getenv("CONTROL_CHANNEL_ID", "1355433803358933042"))
except ValueError:
    logging.error("Channel IDs must be integers.")
    sys.exit(1)

# Modal for sending in-game text
class CustomTextModal(ui.Modal, title="Send In-Game Text"):
    text_input = ui.TextInput(label="Message", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        headers = {"X-API-Key": API_KEY}
        try:
            response = requests.post(
                f"{SCUM_API_URL}/send_text",
                json={"text": self.text_input.value},
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                await interaction.response.send_message(
                    f"Sent: {self.text_input.value}", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"Failed: {response.text}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {str(e)}", ephemeral=True)

# View for bot control buttons
class ControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Send Text", style=discord.ButtonStyle.success, custom_id="send_text")
    async def send_text(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(CustomTextModal())
    
    @ui.button(label="Update Players", style=discord.ButtonStyle.primary, custom_id="update_players")
    async def update_players(self, interaction: discord.Interaction, button: ui.Button):
        headers = {"X-API-Key": API_KEY}
        try:
            response = requests.post(
                f"{SCUM_API_URL}/update_players",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                await interaction.response.send_message("Player update initiated!", ephemeral=True)
            else:
                await interaction.response.send_message(f"Failed: {response.text}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

# View for registration buttons
class RegistrationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Register", style=discord.ButtonStyle.primary, custom_id="register")
    async def register(self, interaction: discord.Interaction, button: ui.Button):
        headers = {"X-API-Key": API_KEY}
        try:
            response = requests.post(
                f"{SCUM_API_URL}/register",
                json={"discord_id": str(interaction.user.id)},
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                code = response.json().get("verification_code")
                await interaction.response.send_message(
                    f"Your code: `{code}`\nType this in-game!", ephemeral=True)
            else:
                await interaction.response.send_message("Registration failed", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
    
    @ui.button(label="Account Info", style=discord.ButtonStyle.secondary, custom_id="account_info")
    async def account_info(self, interaction: discord.Interaction, button: ui.Button):
        headers = {"X-API-Key": API_KEY}
        try:
            response = requests.get(
                f"{SCUM_API_URL}/get_registration",
                params={"discord_id": str(interaction.user.id)},
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                info = (f"Status: {data.get('status', 'unknown')}\n"
                        f"Steam ID: {data.get('steam_id', 'not linked')}\n"
                        f"Verification Code: {data.get('verification_code', 'none')}")
                await interaction.response.send_message(info, ephemeral=True)
            else:
                await interaction.response.send_message("No registration found", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

# Set up bot intents and create the bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    # Setup registration channel
    reg_channel = bot.get_channel(REGISTRATION_CHANNEL_ID)
    if reg_channel:
        await reg_channel.purge(limit=10)
        await reg_channel.send("**Account Registration**", view=RegistrationView())
    else:
        logging.warning(f"Registration channel with ID {REGISTRATION_CHANNEL_ID} not found.")
    # Setup control channel
    control_channel = bot.get_channel(CONTROL_CHANNEL_ID)
    if control_channel:
        await control_channel.purge(limit=10)
        await control_channel.send("**Bot Controls**", view=ControlView())
    else:
        logging.warning(f"Control channel with ID {CONTROL_CHANNEL_ID} not found.")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")
