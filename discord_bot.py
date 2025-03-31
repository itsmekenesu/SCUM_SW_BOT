import discord
from discord.ext import commands
import requests
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

VPS_API_URL = os.getenv("VPS_API_URL", "http://localhost:5000")
VPS_API_KEY = os.getenv("VPS_API_KEY")

@bot.command(name="scum")
@commands.has_role("Admin")  # Restrict to Admin role
async def scum_command(ctx, bot_id: str, action: str):
    valid_actions = ["verify", "status"]
    if action not in valid_actions:
        await ctx.send(f"❌ Invalid action. Use: {', '.join(valid_actions)}")
        return

    command = "send_verification" if action == "verify" else "status_check"
    response = requests.post(
        f"{VPS_API_URL}/bot/command",
        json={"bot_id": bot_id, "command": command},
        headers={"X-API-Key": VPS_API_KEY}
    )
    
    if response.status_code == 200:
        await ctx.send(f"✅ Command '{action}' sent to bot {bot_id}")
    else:
        await ctx.send(f"❌ Error: {response.text}")

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="SCUM Controller"))

# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))
