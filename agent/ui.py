import asyncio
import discord
from config import ADMIN_USER_IDS
from tools.radarr_tools import radarr_grab_release, radarr_add_movie
from tools.sonarr_tools import sonarr_grab_release, sonarr_add_series
from tools.docker_tools import restart_docker_container, update_docker_container
from tools.jellyseerr_tools import jellyseerr_approve_request, jellyseerr_decline_request

def _is_admin_user(user_id: int) -> bool:
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS

class ReleasePickerView(discord.ui.View):
    """Interactive Discord buttons for selecting a release from Radarr or Sonarr search."""
    def __init__(self, releases: list[dict], author_id: int, service: str = "radarr"):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.releases = releases
        self.service = service

        for idx, r in enumerate(releases[:4], start=1):
            btn_label = f"Grab #{idx} ({r.get('quality', 'Rel')}, {r.get('size_gb', 0)}GB)"
            button = discord.ui.Button(
                label=btn_label[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"grab_{idx}"
            )
            button.callback = self._make_grab_callback(r, idx)
            self.add_item(button)

        cancel_btn = discord.ui.Button(
            label="Cancel", 
            style=discord.ButtonStyle.secondary, 
            custom_id="cancel_grab"
        )
        cancel_btn.callback = self._cancel_callback
        self.add_item(cancel_btn)

    def _make_grab_callback(self, release: dict, idx: int):
        async def callback(interaction: discord.Interaction):
            if not _is_admin_user(interaction.user.id):
                await interaction.response.send_message("❌ Only administrators can grab releases.", ephemeral=True)
                return
            await interaction.response.defer()
            
            if self.service == "sonarr":
                res = sonarr_grab_release(guid=release.get("guid", ""), indexer_id=release.get("indexerId", 0))
            else:
                res = radarr_grab_release(guid=release.get("guid", ""), indexer_id=release.get("indexerId", 0))

            if res.get("status") == "success":
                embed = discord.Embed(
                    title="✅ Release Grabbed!",
                    description=f"**{release.get('title')}**\nSize: {release.get('size_gb')} GB | Quality: {release.get('quality')}\nSent to download client successfully by <@{interaction.user.id}>.",
                    color=discord.Color.green()
                )
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.edit_original_response(
                    content=f"❌ Error grabbing release: {res.get('error', 'Unknown error')}",
                    view=None
                )
        return callback

    async def _cancel_callback(self, interaction: discord.Interaction):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can cancel.", ephemeral=True)
            return
        await interaction.response.edit_message(content="🚫 Grab cancelled.", embed=None, view=None)

class ContainerRestartConfirmView(discord.ui.View):
    """Confirmation button for restarting Docker containers."""
    def __init__(self, container_name: str, author_id: int):
        super().__init__(timeout=60)
        self.container_name = container_name
        self.author_id = author_id

    @discord.ui.button(label="Confirm Restart", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can restart containers.", ephemeral=True)
            return
        await interaction.response.defer()
        res = restart_docker_container(self.container_name)
        if res.get("status") == "success":
            embed = discord.Embed(
                title="🔄 Container Restarted",
                description=f"Container **`{self.container_name}`** was restarted successfully by <@{interaction.user.id}>.",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed, view=None)
        else:
            await interaction.edit_original_response(
                content=f"❌ Failed to restart container: {res.get('error')}", 
                view=None
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can cancel.", ephemeral=True)
            return
        await interaction.response.edit_message(content="🚫 Restart cancelled.", embed=None, view=None)

from tools.jellyseerr_tools import jellyseerr_approve_request, jellyseerr_decline_request, jellyseerr_request_media

class JellyseerrApprovalView(discord.ui.View):
    """Interactive approval buttons for Jellyseerr requests. Gated strictly to admins."""
    def __init__(self, title: str, media_type: str = "movie", request_id: int = None, media_id: int = None):
        super().__init__(timeout=300)
        self.title = title
        self.media_type = media_type
        self.request_id = request_id
        self.media_id = media_id

    @discord.ui.button(label="Approve Request", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can approve media requests.", ephemeral=True)
            return
        await interaction.response.defer()
        
        if self.request_id:
            res = jellyseerr_approve_request(self.request_id)
        else:
            res = jellyseerr_request_media(title=self.title, media_type=self.media_type, force_submit=True)

        if res.get("status") in ["success", "approved"]:
            embed = discord.Embed(
                title="✅ Request Approved",
                description=f"Media request for **{self.title}** was approved by <@{interaction.user.id}>.\nSent to Radarr/Sonarr to start downloading.",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed, view=None)
        else:
            await interaction.edit_original_response(content=f"❌ Error approving request: {res.get('error')}", view=None)

    @discord.ui.button(label="Decline Request", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can decline media requests.", ephemeral=True)
            return
        await interaction.response.defer()
        if self.request_id:
            jellyseerr_decline_request(self.request_id)
            
        embed = discord.Embed(
            title="🚫 Request Declined",
            description=f"Media request for **{self.title}** was declined by <@{interaction.user.id}>.",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=None)

class AdminDirectAddView(discord.ui.View):
    """Interactive button sent to Admin DM when Jellyseerr misses a title but Radarr/Sonarr finds it."""
    def __init__(self, title: str, media_type: str, item_id: int, requested_by: str = "A user"):
        super().__init__(timeout=86400) # 24 hours
        self.title = title
        self.media_type = media_type
        self.item_id = item_id
        self.requested_by = requested_by

    @discord.ui.button(label="Approve & Download", style=discord.ButtonStyle.success)
    async def add_and_download(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can add media.", ephemeral=True)
            return
        await interaction.response.defer()

        if self.media_type == "tv":
            res = sonarr_add_series(tvdb_id=self.item_id, search_now=True)
        else:
            res = radarr_add_movie(tmdb_id=self.item_id, search_now=True)

        if res.get("status") == "success":
            embed = discord.Embed(
                title="✅ Media Added & Search Triggered",
                description=(
                    f"**{self.title}** was added directly to {'Sonarr' if self.media_type == 'tv' else 'Radarr'} by <@{interaction.user.id}>.\n"
                    f"Originally requested by: **{self.requested_by}**"
                ),
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed, view=None)
        else:
            await interaction.edit_original_response(
                content=f"❌ Failed to add media: {res.get('error')}", 
                view=None
            )

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.secondary)
    async def dismiss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can dismiss.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"🚫 Request for **{self.title}** dismissed.", embed=None, view=None)

class ContainerUpdateConfirmView(discord.ui.View):
    """Interactive Discord buttons for 1-click container update and recreation."""
    def __init__(self, container_name: str, author_id: int):
        super().__init__(timeout=86400)  # 24 hour timeout
        self.container_name = container_name
        self.author_id = author_id

    @discord.ui.button(label="Update Now", style=discord.ButtonStyle.success, emoji="🚀")
    async def update(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can trigger container updates.", ephemeral=True)
            return

        # Disable button to prevent duplicate clicks
        button.disabled = True
        button.label = "Updating..."
        await interaction.response.edit_message(view=self)

        status_msg = await interaction.followup.send(
            f"⏳ Pulling latest image and recreating **`{self.container_name}`** via Docker Compose...",
            ephemeral=False
        )

        res = await asyncio.to_thread(update_docker_container, self.container_name)

        if res.get("status") == "success":
            embed = discord.Embed(
                title="✅ Container Updated",
                description=(
                    f"Container **`{self.container_name}`** was updated and recreated successfully by <@{interaction.user.id}>!\n\n"
                    f"```\n{res.get('output', '').strip()[:1000]}\n```"
                ),
                color=discord.Color.green()
            )
            await status_msg.edit(content=None, embed=embed)
            button.label = "Updated"
            button.style = discord.ButtonStyle.secondary
            await interaction.edit_original_response(view=self)
        else:
            embed = discord.Embed(
                title="❌ Update Failed",
                description=f"Error updating **`{self.container_name}`**:\n```\n{res.get('error', 'Unknown error')[:1000]}\n```",
                color=discord.Color.red()
            )
            await status_msg.edit(content=None, embed=embed)
            button.disabled = False
            button.label = "Retry Update"
            button.style = discord.ButtonStyle.danger
            await interaction.edit_original_response(view=self)

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.secondary)
    async def dismiss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _is_admin_user(interaction.user.id):
            await interaction.response.send_message("❌ Only administrators can dismiss.", ephemeral=True)
            return
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

