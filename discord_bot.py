import discord
from discord.ext import commands
import requests
import os

# Initialize bot with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Explicitly define BOT_TOKEN for import
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="!", intents=intents)

# API configuration
VPS_API_URL = os.getenv("VPS_API_URL", "http://localhost:8079")
VPS_API_KEY = os.getenv("VPS_API_KEY")

@bot.command(name="scum")
@commands.has_role("Admin")
async def scum_command(ctx, bot_id: str, action: str):
    """Handle SCUM bot commands"""
    try:
        await ctx.defer(ephemeral=True)
    except discord.NotFound:
        await ctx.send("⚠️ Command timed out! Try again.")
        return

    valid_actions = ["verify", "status"]
    
    if action not in valid_actions:
        await ctx.followup.send(f"❌ Invalid action. Use: {', '.join(valid_actions)}")
        return

    try:
        command = "send_verification" if action == "verify" else "status_check"
        response = requests.post(
            f"{VPS_API_URL}/bot/command",
            json={"bot_id": bot_id, "command": command},
            headers={"X-API-Key": VPS_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            await ctx.followup.send(f"✅ Command '{action}' sent to {bot_id}")
        else:
            await ctx.followup.send(f"❌ API Error: {response.text}")
            
    except Exception as e:
        await ctx.followup.send(f"🔥 Error: {str(e)}")

@bot.event
async def on_ready():
    print(f"🤖 Connected as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="SCUM Control Panel"))
