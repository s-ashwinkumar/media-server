# Discord Media Server AI Agent

A lightweight, token-efficient AI agent that connects to Discord to provide remote management, health checks, and interactive media resolution for your Radarr, Sonarr, qBittorrent, and Docker media server stack.

---

## Features

* **Interactive Radarr & Sonarr Release Resolution (Admin Only):**
  * Search movies/shows, inspect stalled downloads, query alternative indexer releases.
  * Interactive Discord buttons (`[Grab 1080p]`, `[Grab 4K]`, `[Cancel]`) to resolve releases with 1 click.
* **Server Health & Monitoring (Admin Only):**
  * Check disk space across `/`, `/media/movies`, `/media/tv-series`, and cold storage pools.
  * Real-time CPU, RAM, and Docker container health checks (`!status`, `!disk`).
* **Container Management (Admin Only):**
  * Restart containers (`jellyfin`, `qbittorrent`, `surfshark`, etc.) with interactive confirmation buttons.
* **Safe Read-Only Search for Regular Users:**
  * Friends/family can ask if movies or shows exist in the library, while all admin tools and server commands are completely hidden.
* **High Token Efficiency:**
  * Data filtering happens in Python before sending summaries to OpenRouter.
  * Average cost per interaction: `< $0.0005` with `google/gemini-2.0-flash` or `deepseek/deepseek-chat`.
* **2-Tier Role-Based Access Control:**
  * Hard security in Python: non-admin users never have admin tool schemas injected into the LLM prompt.

---

## Access Control Tiers

| Capability | Admin (`DISCORD_ADMIN_USER_IDS`) | Regular Users (`DISCORD_ALLOWED_USER_IDS`) | Unlisted Users |
| :--- | :---: | :---: | :---: |
| Search Movies / TV Shows | ✅ | ✅ | ❌ *(Ignored)* |
| Check Media Status in Library | ✅ | ✅ | ❌ *(Ignored)* |
| Grab Releases / Resolve Downloads | ✅ *(Interactive Buttons)* | ❌ *(Tool Hidden)* | ❌ *(Ignored)* |
| Restart Docker Containers | ✅ *(Confirmation Buttons)* | ❌ *(Tool Hidden)* | ❌ *(Ignored)* |
| View Container Logs & Health | ✅ | ❌ *(Tool Hidden)* | ❌ *(Ignored)* |
| View Disk Storage Pools | ✅ | ❌ *(Tool Hidden)* | ❌ *(Ignored)* |

---

## Setup Guide

### 1. Create your Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Go to the **Bot** tab:
   * Click **Reset Token** to copy your `DISCORD_BOT_TOKEN`.
   * Under **Privileged Gateway Intents**, turn ON **Message Content Intent**.
3. Go to **OAuth2 $\rightarrow$ URL Generator**:
   * Scopes: Select `bot`.
   * Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`, `Use Slash Commands`.
   * Open the generated URL in your browser to invite the bot to your Discord server.
4. Copy your personal Discord User ID:
   * In Discord settings: Advanced $\rightarrow$ enable **Developer Mode**.
   * Right-click your username in chat $\rightarrow$ **Copy User ID**.

### 2. Configure Environment

Copy the `.env.example` in `agent/` to `agent/.env`:

```bash
cd /home/mediaserver/code/media-server/agent
cp .env.example .env
```

Edit `agent/.env` with your tokens:
```ini
DISCORD_BOT_TOKEN=your_token_here
DISCORD_ADMIN_USER_IDS=your_discord_user_id_here
DISCORD_ALLOWED_USER_IDS=your_discord_user_id_here,optional_family_user_id
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```
*(Radarr, Sonarr, and qBittorrent credentials are automatically imported from `../compose_files/.env`)*.

### 3. Install Dependencies & Run

```bash
cd /home/mediaserver/code/media-server/agent
pip install -r requirements.txt
python3 bot.py
```

### 4. (Optional) Run as a Background Systemd Service

To keep the bot running automatically on server boot:

```bash
sudo cp /home/mediaserver/code/media-server/agent/media-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now media-agent
sudo systemctl status media-agent
```

---

## How to Interact in Discord

* **Admin Usage (DMs or private `#server-admin` channel):**
  * *"Why is Dune 2 not downloading? Can you find a better copy with more seeds?"*
  * *"How much free space do I have left on movies?"*
  * *"Restart Jellyfin container."*
  * Quick Commands: `!status`, `!disk`
* **Non-Admin Usage (e.g. in a shared `#media` channel):**
  * *"Do we have the TV show Severance?"*
  * *"Is Inception available in 4K?"*
