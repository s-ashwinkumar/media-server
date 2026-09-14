import logging
import discord
import asyncio
from discord.ext import commands, tasks
from aiohttp import web

from config import (
    DISCORD_BOT_TOKEN, 
    ADMIN_USER_IDS, 
    ALLOWED_USER_IDS, 
    AUTO_REPLY_CHANNEL_IDS,
    AUTO_REPLY_CHANNEL_NAMES
)
from llm import ask_agent
from ui import (
    ReleasePickerView, 
    ContainerRestartConfirmView, 
    JellyseerrApprovalView, 
    AdminDirectAddView, 
    ContainerUpdateConfirmView
)
from tools.system_tools import get_disk_space, get_system_stats
from tools.docker_tools import list_docker_containers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("media_agent")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory conversation history: {channel_or_user_id: [{"role": "user"/"assistant", "content": ...}]}
conversation_histories = {}

def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS or user_id in ADMIN_USER_IDS

def is_admin(user_id: int) -> bool:
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS

async def notify_admins(title: str, description: str, color: discord.Color = discord.Color.red(), prefix: str = "🚨 ", view_factory=None):
    """Send an alert DM to all configured administrators."""
    for admin_id in ADMIN_USER_IDS:
        try:
            user = await bot.fetch_user(admin_id)
            if user:
                embed = discord.Embed(
                    title=f"{prefix}{title}".strip(),
                    description=description,
                    color=color
                )
                if view_factory:
                    view = view_factory(admin_id)
                    await user.send(embed=embed, view=view)
                else:
                    await user.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send DM alert to admin {admin_id}: {e}")

async def handle_wud_webhook(request: web.Request):
    """Handle incoming webhook POST requests from What's Up Docker (WUD)."""
    try:
        data = await request.json()
        logger.info("Received WUD webhook event")
    except Exception as e:
        logger.error(f"Error parsing WUD webhook JSON: {e}")
        return web.json_response({"error": "Invalid JSON"}, status=400)

    try:
        if isinstance(data, list):
            containers = data
        elif isinstance(data, dict):
            if "container" in data and isinstance(data["container"], dict):
                containers = [data["container"]]
            elif "containers" in data and isinstance(data["containers"], list):
                containers = data["containers"]
            else:
                containers = [data]
        else:
            return web.json_response({"error": "Invalid payload format"}, status=400)

        for container in containers:
            name = container.get("displayName") or container.get("name") or "Unknown Container"
            image_info = container.get("image", {})
            if isinstance(image_info, dict):
                image_name = image_info.get("name", "")
                tag_dict = image_info.get("tag", {})
                current_tag = tag_dict.get("value", "latest") if isinstance(tag_dict, dict) else str(tag_dict)
                digest_dict = image_info.get("digest", {})
                current_digest = digest_dict.get("value", "") if isinstance(digest_dict, dict) else str(digest_dict)
            else:
                image_name = str(image_info)
                current_tag = "latest"
                current_digest = ""

            result_info = container.get("result", {})
            if isinstance(result_info, dict):
                new_tag = result_info.get("tag") or current_tag
                new_digest = result_info.get("digest", "")
            else:
                new_tag = current_tag
                new_digest = ""

            update_kind = container.get("updateKind", {})
            if isinstance(update_kind, dict):
                kind_str = update_kind.get("kind", "new image")
                semver_diff = update_kind.get("semverDiff")
                kind_display = f"{kind_str} ({semver_diff})" if semver_diff else kind_str
            else:
                kind_display = "new image"

            desc_lines = [
                f"A new Docker update was detected by **What's Up Docker**:\n",
                f"• **Container:** `{name}`",
                f"• **Image:** `{image_name}:{new_tag}`",
                f"• **Update Detail:** `{kind_display}`",
            ]

            if current_digest and new_digest and current_digest != new_digest:
                short_curr = current_digest[:19] + "..." if len(current_digest) > 20 else current_digest
                short_new = new_digest[:19] + "..." if len(new_digest) > 20 else new_digest
                desc_lines.append(f"• **Current Digest:** `{short_curr}`")
                desc_lines.append(f"• **New Digest:** `{short_new}`")

            desc_lines.append(f"\n💡 *Tap **Update Now** below to pull & recreate via Docker Compose, or review on [What's Up Docker](http://wud.kewpie.top).*")

            await notify_admins(
                title=f"Container Update: {name}",
                description="\n".join(desc_lines),
                color=discord.Color.blue(),
                prefix="📦 ",
                view_factory=lambda uid, cname=name: ContainerUpdateConfirmView(container_name=cname, author_id=uid)
            )

        return web.json_response({"status": "ok", "processed": len(containers)})
    except Exception as e:
        logger.error(f"Error handling WUD webhook: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)

async def handle_wud_health(request: web.Request):
    """Health check endpoint for the webhook server."""
    return web.json_response({"status": "ok", "service": "kewpie-wud-webhook"})

async def start_webhook_server():
    """Start local aiohttp server to listen for WUD webhooks on port 8088."""
    try:
        app = web.Application()
        app.router.add_post('/wud-webhook', handle_wud_webhook)
        app.router.add_get('/wud-webhook', handle_wud_health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8088)
        await site.start()
        logger.info("WUD Webhook HTTP server started on http://0.0.0.0:8088/wud-webhook")
    except Exception as e:
        logger.error(f"Failed to start WUD webhook server: {e}", exc_info=True)

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

    if not getattr(bot, "_wud_server_started", False):
        bot._wud_server_started = True
        asyncio.create_task(start_webhook_server())

    print(f"\n==========================================")
    print(f" Media Server Agent is Online as: {bot.user}")
    print(f" Admin User IDs: {ADMIN_USER_IDS or 'All (No admin whitelist set)'}")
    print(f" General Access: {'Open to all server members' if not ALLOWED_USER_IDS else ALLOWED_USER_IDS}")
    print(f" Auto-Reply Channels: {', '.join(['#' + n for n in AUTO_REPLY_CHANNEL_NAMES]) if AUTO_REPLY_CHANNEL_NAMES else ''} {AUTO_REPLY_CHANNEL_IDS if AUTO_REPLY_CHANNEL_IDS else ''}")
    print(f" Webhook Server: http://0.0.0.0:8088/wud-webhook")
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

@bot.command(name="update")
async def cmd_update(ctx, container_name: str = None):
    """Pull latest image and recreate a container service (Admin only)."""
    if not is_admin(ctx.author.id):
        await ctx.send("❌ This command is restricted to administrators.")
        return
    if not container_name:
        await ctx.send("❌ Please specify a container name, e.g. `!update jellyfin`")
        return

    name = container_name.lower().strip()
    view = ContainerUpdateConfirmView(container_name=name, author_id=ctx.author.id)
    await ctx.send(
        f"Click **Update Now** to pull the latest image and recreate **`{name}`** via Docker Compose:",
        view=view
    )

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

    # Check activation triggers: DM, mention, dedicated channel, or reply to bot
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    
    channel_name = getattr(message.channel, "name", "").lower().strip()
    is_auto_reply_channel = (
        message.channel.id in AUTO_REPLY_CHANNEL_IDS or 
        channel_name in AUTO_REPLY_CHANNEL_NAMES
    )

    is_reply_to_bot = False
    if message.reference and message.reference.message_id:
        try:
            ref_msg = message.reference.resolved
            if ref_msg is None or isinstance(ref_msg, discord.DeletedReferencedMessage):
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
            if ref_msg and ref_msg.author == bot.user:
                is_reply_to_bot = True
        except Exception:
            pass

    if not (is_dm or is_mentioned or is_auto_reply_channel or is_reply_to_bot):
        return

    # Strip bot mention from content
    clean_content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
    if not clean_content:
        await message.reply("👋 How can I help you with your media server?")
        return

    # Capture ambient channel context (recent messages before this one) so the bot understands references
    ambient_context = ""
    if not is_dm and hasattr(message.channel, "history"):
        try:
            prev_msgs = []
            async for prev in message.channel.history(limit=6, before=message):
                if prev.author == bot.user or not prev.content.strip():
                    continue
                prev_msgs.append(f"{prev.author.display_name}: {prev.content.strip()}")
            if prev_msgs:
                prev_msgs.reverse()
                ambient_context = "\n".join(prev_msgs)
        except Exception as e:
            logger.debug(f"Could not retrieve ambient context: {e}")

    async with message.channel.typing():
        user_id = message.author.id
        user_is_admin = is_admin(user_id)
        
        # Track history per channel (for shared context) or per user in DMs
        history_key = message.channel.id if not is_dm else user_id
        history = conversation_histories.get(history_key, [])

        try:
            # Run agent with LLM
            agent_response = await ask_agent(
                user_prompt=clean_content, 
                is_admin=user_is_admin, 
                conversation_history=history,
                ambient_context=ambient_context
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
        conversation_histories[history_key] = history[-8:]

        # Handle silent fallback to Radarr/Sonarr (DM to Admin with 1-click add button)
        admin_fallback = agent_response.get("admin_fallback")
        if admin_fallback and isinstance(admin_fallback, dict):
            fb_view = AdminDirectAddView(
                title=admin_fallback.get("title", "Media"),
                media_type=admin_fallback.get("mediaType", "movie"),
                item_id=admin_fallback.get("id"),
                requested_by=message.author.display_name
            )
            service_name = "Sonarr" if admin_fallback.get("mediaType") == "tv" else "Radarr"
            for admin_id in ADMIN_USER_IDS:
                try:
                    admin_user = await bot.fetch_user(admin_id)
                    if admin_user:
                        embed = discord.Embed(
                            title="📥 Fallback Media Request",
                            description=(
                                f"**{message.author.mention}** (`{message.author.display_name}`) requested **{admin_fallback.get('title')}** ({admin_fallback.get('year', '')}).\n\n"
                                f"It was not found in Jellyseerr's public catalog, but was matched in **{service_name}** indexers.\n\n"
                                f"Click below to approve and start downloading."
                            ),
                            color=discord.Color.blue()
                        )
                        await admin_user.send(embed=embed, view=fb_view)
                except Exception as e:
                    logger.error(f"Failed to send admin fallback DM to {admin_id}: {e}")

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
