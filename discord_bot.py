import discord
from discord.ext import commands
import requests
import os

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for command interactions
intents.members = True          # Required for role checks

bot = commands.Bot(command_prefix="!", intents=intents)

VPS_API_URL = os.getenv("VPS_API_URL", "http://localhost:8079")
VPS_API_KEY = os.getenv("VPS_API_KEY")

@bot.command(name="scum")
@commands.has_role("Admin")
async def scum_command(ctx, bot_id: str, action: str):
    """Handle SCUM bot commands"""
    try:
        # Immediately defer the response
        await ctx.defer(ephemeral=True)
    except discord.NotFound:
        await ctx.send("⚠️ Interaction timed out! Please try again.")
        return

    valid_actions = ["verify", "status"]
    
    if action not in valid_actions:
        await ctx.followup.send(
            f"❌ Invalid action. Valid options: {', '.join(valid_actions)}"
        )
        return

    try:
        # Send command to VPS API
        command = "send_verification" if action == "verify" else "status_check"
        response = requests.post(
            f"{VPS_API_URL}/bot/command",
            json={"bot_id": bot_id, "command": command},
            headers={"X-API-Key": VPS_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            await ctx.followup.send(
                f"✅ Command '{action}' executed for bot {bot_id}"
            )
        else:
            await ctx.followup.send(
                f"❌ API Error ({response.status_code}): {response.text}"
            )
            
    except requests.Timeout:
        await ctx.followup.send("⌛ Command timed out - try again later")
    except Exception as e:
        await ctx.followup.send(f"🔥 Critical error: {str(e)}")
        raise e

@bot.event
async def on_ready():
    print(f"🤖 Connected as {bot.user.name} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Game(name="SCUM Management")
    )

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
