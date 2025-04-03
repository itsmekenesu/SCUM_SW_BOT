import discord
from discord import app_commands
from discord.ext import commands
import os
import requests

# Ensure API_URL includes your base URL; the Discord bot will append /api to its calls.
API_URL = os.getenv('VPS_API_URL')
API_KEY = os.getenv('VPS_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')  # This webhook should post to channel 1355434230594666594
AUTHORIZED_USER_ID = 912964118447816735  # Only allow this Discord user

def send_update(message: str):
    try:
        requests.post(DISCORD_WEBHOOK, json={'content': message}, timeout=5)
    except Exception as e:
        print(f"Failed to send update to webhook: {e}")

def process_scum_command(user: discord.User, bot_id: str, command: str) -> (bool, str):
    try:
        response = requests.post(
            f"{API_URL}/api/bot/command",  # Note the /api prefix
            json={
                "bot_id": bot_id,
                "command": {
                    "type": "discord_command",
                    "content": command,
                    "user": str(user)
                }
            },
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        if response.status_code == 200:
            send_update(f"Command sent to bot {bot_id} by {user}.")
            return True, f"✅ Command sent to bot {bot_id}"
        else:
            error_msg = response.json().get('error', 'Unknown error')
            send_update(f"Error sending command to bot {bot_id} by {user}: {error_msg}")
            return False, f"❌ Error: {error_msg}"
    except Exception as e:
        send_update(f"Connection failed when sending command by {user}: {str(e)}")
        return False, f"🚨 Connection failed: {str(e)}"

class ScumBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
    async def setup_hook(self):
        await self.tree.sync()

bot = ScumBot()

@bot.tree.command(name="scum", description="Manage SCUM bots. Use: /scum bot_id:<id> command:<cmd>")
@app_commands.describe(bot_id="Target bot ID", command="Command to send (verify, status, or say <message>)")
async def scum_slash(interaction: discord.Interaction, bot_id: str, command: str):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        send_update(f"Unauthorized command attempt by {interaction.user} (ID: {interaction.user.id}).")
        return

    await interaction.response.defer(ephemeral=True)
    success, result_message = process_scum_command(interaction.user, bot_id, command)
    await interaction.followup.send(result_message, ephemeral=True)

@bot.command(name="scum")
async def scum_text(ctx, bot_id: str, *, command: str):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("❌ You are not authorized to use this command.", delete_after=10)
        send_update(f"Unauthorized command attempt by {ctx.author} (ID: {ctx.author.id}).")
        return
    success, result_message = process_scum_command(ctx.author, bot_id, command)
    await ctx.send(result_message, delete_after=10)

@bot.tree.command(name="help", description="Show instructions on how to use the bot.")
async def help_slash(interaction: discord.Interaction):
    help_text = (
        "**SCUM Bot Help**\n\n"
        "Use the following commands:\n"
        "• `/scum bot_id:<id> command:verify` - Send a verification message.\n"
        "• `/scum bot_id:<id> command:status` - Request a status check.\n"
        "• `/scum bot_id:<id> command:say <message>` - Have the bot send a chat message.\n\n"
        "You can also use these commands with the `!` prefix, e.g., `!scum <bot_id> verify`.\n"
        "Only the authorized user can use these commands."
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.command(name="help")
async def help_text(ctx):
    help_text = (
        "**SCUM Bot Help**\n\n"
        "Use the following commands:\n"
        "• `!scum <bot_id> verify` - Send a verification message.\n"
        "• `!scum <bot_id> status` - Request a status check.\n"
        "• `!scum <bot_id> say <message>` - Have the bot send a chat message.\n\n"
        "You can also use slash commands (e.g., `/scum`).\n"
        "Only the authorized user can use these commands."
    )
    await ctx.send(help_text, delete_after=20)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    send_update(f"✅ SCUM Bot connected as {bot.user}")

@bot.event
async def on_disconnect():
    send_update("⚠️ SCUM Bot connection lost.")

@bot.event
async def on_resumed():
    send_update("🔄 SCUM Bot reconnected/resumed.")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
