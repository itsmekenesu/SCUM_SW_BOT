import os
import requests
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

VPS_API_URL = os.getenv("VPS_API_URL")
API_KEY = os.getenv("VPS_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Discord bot logged in as {bot.user}")

@bot.command(name="say")
async def say(ctx, *, message: str):
    payload = {"command": f"say {message}"}
    try:
        response = requests.post(
            f"{VPS_API_URL}/send_command",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        await ctx.send(f"Command forwarded to bot {data.get('bot_id')}. Response: {data.get('bot_response')}")
    except Exception as e:
        logging.error(f"Failed to send command: {str(e)}")
        await ctx.send("Failed to send command. Are bots online?")

@bot.command(name="status")
async def status(ctx):
    payload = {"command": "status"}
    try:
        response = requests.post(
            f"{VPS_API_URL}/send_command",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        await ctx.send(f"Bot {data.get('bot_id')} status: {data.get('bot_response')}")
    except Exception as e:
        logging.error(f"Failed to get status: {str(e)}")
        await ctx.send("Failed to get bot status.")

def run_discord_bot():
    bot.run(BOT_TOKEN)
