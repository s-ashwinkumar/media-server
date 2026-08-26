import logging
import discord
import asyncio
from discord.ext import commands, tasks

from config import DISCORD_BOT_TOKEN, ADMIN_USER_IDS, ALLOWED_USER_IDS
from llm import ask_agent
from ui import ReleasePickerView, ContainerRestartConfirmView, JellyseerrApprovalView
from tools.system_tools import get_disk_space, get_system_stats
from tools.docker_tools import list_docker_containers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("media_agent")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory short conversation history per user: {user_id: [{"role": "user"/"assistant", "content": ...}]}
user_histories = {}

def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS or user_id in ADMIN_USER_IDS

def is_admin(user_id: int) -> bool:
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS

async def notify_admins(title: str, description: str, color: discord.Color = discord.Color.red()):
    """Send an alert DM to all configured administrators."""
    for admin_id in ADMIN_USER_IDS:
        try:
            user = await bot.fetch_user(admin_id)
            if user:
                embed = discord.Embed(
                    title=f"🚨 {title}",
                    description=description,
                    color=color
                )
                await user.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send DM alert to admin {admin_id}: {e}")

@tasks.loop(minutes=30)
async def disk_health_monitor():
    """Periodically check storage pools and DM admins if storage exceeds 90%."""
    try:
        pools = get_disk_space()
        for p in pools:
            if "error" in p:
                continue
            pct_str = p.get("percent_used", "0%").replace("%", "").strip()
            try:
                pct = float(pct_str)
            except ValueError:
                continue
            if pct >= 90.0:
                await notify_admins(
                    title="Storage Space Warning (>90%)",
                    description=(
                        f"**Storage Pool:** `{p.get('storage_pool')}`\n"
                        f"**Usage:** {p.get('used_gb')} / {p.get('total_gb')} GB (**{p.get('percent_used')}**)\n"
                        f"**Remaining:** **{p.get('free_gb')} GB free**\n\n"
                        f"⚠️ *Please consider cleaning up incomplete downloads or old media files.*"
                    ),
                    color=discord.Color.gold()
                )
    except Exception as e:
        logger.error(f"Error in disk health monitor: {e}")

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    activity = discord.Activity(type=discord.ActivityType.watching, name="over your Media Server")
    await bot.change_presence(activity=activity)
    if not disk_health_monitor.is_running():
        disk_health_monitor.start()
    print(f"\n==========================================")
    print(f" Media Server Agent is Online as: {bot.user}")
    print(f" Admin User IDs: {ADMIN_USER_IDS or 'All (No admin whitelist set)'}")
    print(f" General Access: {'Open to all server members' if not ALLOWED_USER_IDS else ALLOWED_USER_IDS}")
    print(f"==========================================\n")

@bot.command(name="status")
async def cmd_status(ctx):
    """Quick overview of Docker containers and system health (Admin only)."""
    if not is_admin(ctx.author.id):
        await ctx.send("❌ This command is restricted to administrators.")
        return

    containers = list_docker_containers()
    stats = get_system_stats()

    running = [c['name'] for c in containers if c.get('status') == 'running']
    stopped = [c['name'] for c in containers if c.get('status') != 'running']

    embed = discord.Embed(title="🖥️ Media Server Health", color=discord.Color.blue())
    embed.add_field(name="CPU Usage", value=stats.get("cpu_usage_percent", "N/A"), inline=True)
    embed.add_field(name="Memory", value=f"{stats.get('memory_used_gb', 0)} / {stats.get('memory_total_gb', 0)} GB ({stats.get('memory_percent', 'N/A')})", inline=True)
    embed.add_field(name=f"🟢 Running ({len(running)})", value=", ".join(running[:10]) or "None", inline=False)
    if stopped:
        embed.add_field(name=f"🔴 Stopped ({len(stopped)})", value=", ".join(stopped[:10]), inline=False)

    await ctx.send(embed=embed)

@bot.command(name="disk")
async def cmd_disk(ctx):
    """Quick overview of storage pools (Admin only)."""
    if not is_admin(ctx.author.id):
        await ctx.send("❌ This command is restricted to administrators.")
        return

    pools = get_disk_space()
    embed = discord.Embed(title="💾 Storage Pools", color=discord.Color.purple())
    for p in pools:
        if "error" in p:
            continue
        embed.add_field(
            name=f"📁 {p.get('storage_pool')}",
            value=f"{p.get('used_gb')} / {p.get('total_gb')} GB ({p.get('percent_used')}) — **{p.get('free_gb')} GB free**",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == bot.user:
        return

    # Check authorization
    if not is_authorized(message.author.id):
        return

    # Let registered commands process first
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # Check if message is a DM or mentions the bot
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if is_dm or is_mentioned:
        # Strip bot mention from content
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            await message.reply("👋 How can I help you with your media server?")
            return

        async with message.channel.typing():
            user_id = message.author.id
            user_is_admin = is_admin(user_id)
            history = user_histories.get(user_id, [])

            try:
                # Run agent with LLM
                agent_response = await ask_agent(
                    user_prompt=clean_content, 
                    is_admin=user_is_admin, 
                    conversation_history=history
                )
            except Exception as e:
                error_msg = f"❌ An internal error occurred while processing your request: `{str(e)}`"
                logger.error(f"Error processing message from {message.author}: {e}", exc_info=True)
                await message.reply(error_msg)
                # Alert admin via DM
                await notify_admins(
                    title="Bot Processing Exception",
                    description=(
                        f"**User:** {message.author.mention} (`{message.author.name}`)\n"
                        f"**Channel:** {message.channel.mention if hasattr(message.channel, 'mention') else 'DM'}\n"
                        f"**Prompt:** `{clean_content}`\n\n"
                        f"**Error Details:**\n```{str(e)}```"
                    )
                )
                return

            reply_text = agent_response.get("text", "")
            releases_data = agent_response.get("releases_found")
            restart_target = agent_response.get("restart_container_target")

            # If response explicitly contains an error, alert admin
            if reply_text.startswith("❌") or reply_text.startswith("⚠️"):
                await notify_admins(
                    title="Service/API Issue Reported",
                    description=(
                        f"**User:** {message.author.mention} (`{message.author.name}`)\n"
                        f"**Prompt:** `{clean_content}`\n\n"
                        f"**Reported Response:**\n{reply_text[:1500]}"
                    ),
                    color=discord.Color.orange()
                )

            # Update conversation history
            history.append({"role": "user", "content": clean_content})
            history.append({"role": "assistant", "content": reply_text})
            user_histories[user_id] = history[-8:]

            pending_req = agent_response.get("pending_request")

            # Choose UI view if applicable
            view = None
            if pending_req and isinstance(pending_req, dict):
                view = JellyseerrApprovalView(
                    title=pending_req.get("title", "Media"),
                    media_type=pending_req.get("mediaType", "movie"),
                    request_id=pending_req.get("request_id"),
                    media_id=pending_req.get("mediaId")
                )
            elif user_is_admin:
                if releases_data and isinstance(releases_data, dict):
                    view = ReleasePickerView(
                        releases=releases_data.get("items", []), 
                        author_id=user_id,
                        service=releases_data.get("service", "radarr")
                    )
                elif restart_target:
                    view = ContainerRestartConfirmView(container_name=restart_target, author_id=user_id)

            # Discord message character limit check (2000 chars)
            if len(reply_text) > 1950:
                chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
                for i, chunk in enumerate(chunks):
                    if i == len(chunks) - 1 and view:
                        await message.reply(chunk, view=view)
                    else:
                        await message.reply(chunk)
            else:
                await message.reply(reply_text, view=view)

def main():
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN is not set.")
        print("Please configure DISCORD_BOT_TOKEN in agent/.env")
        return
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
