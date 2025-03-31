#!/usr/bin/env python3
import os
import sys
import logging
import discord
from discord.ext import commands
from discord import ui
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# Retrieve required environment variables
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    logging.error("DISCORD_TOKEN is not set.")
    sys.exit(1)

API_KEY = os.getenv("SCUM_API_KEY", "default_secret_key")
SCUM_API_URL = os.getenv("SCUM_API_URL", "http://localhost:5000")

try:
    REGISTRATION_CHANNEL_ID = int(os.getenv("REGISTRATION_CHANNEL_ID", "1355434230594666594"))
    CONTROL_CHANNEL_ID = int(os.getenv("CONTROL_CHANNEL_ID", "1355433803358933042"))
except ValueError:
    logging.error("Channel IDs must be integers.")
    sys.exit(1)

# (Your bot code continues here, including Modal and View classes)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    # Setup channels and send initial messages

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
