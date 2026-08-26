import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
AGENT_DIR = Path(__file__).resolve().parent
REPO_DIR = AGENT_DIR.parent
COMPOSE_ENV_PATH = REPO_DIR / "compose_files" / ".env"
AGENT_ENV_PATH = AGENT_DIR / ".env"

# Load compose_files/.env first, then agent/.env (agent overrides compose)
if COMPOSE_ENV_PATH.exists():
    load_dotenv(COMPOSE_ENV_PATH)
if AGENT_ENV_PATH.exists():
    load_dotenv(AGENT_ENV_PATH, override=True)

# Discord settings
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()

# Access Control: Admins (Full access: Docker restarts, grabbing releases, stats)
admin_users_raw = os.getenv("DISCORD_ADMIN_USER_IDS", "")
ADMIN_USER_IDS = set()
for uid in admin_users_raw.split(","):
    cleaned = uid.strip()
    if cleaned.isdigit():
        ADMIN_USER_IDS.add(int(cleaned))

# Access Control: Optional Whitelist for Regular Users
# If left empty, ANY member in your private Discord server can talk to the bot (with non-admin permissions).
allowed_users_raw = os.getenv("DISCORD_ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = set()
for uid in allowed_users_raw.split(","):
    cleaned = uid.strip()
    if cleaned.isdigit():
        ALLOWED_USER_IDS.add(int(cleaned))

# LLM / OpenRouter settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Priority Cascade
models_raw = os.getenv("OPENROUTER_MODELS", "google/gemini-3.6-flash,google/gemini-3.5-flash,deepseek/deepseek-chat,openrouter/auto")
OPENROUTER_MODELS = [m.strip() for m in models_raw.split(",") if m.strip()]
PRIMARY_MODEL = OPENROUTER_MODELS[0] if OPENROUTER_MODELS else "google/gemini-3.6-flash"

# Service Endpoints and API Keys
RADARR_URL = os.getenv("RADARR_URL", "http://localhost:7878").rstrip("/")
RADARR_API_KEY = os.getenv("RADARR_API_KEY", os.getenv("HOMEPAGE_VAR_RADARR_API_KEY", "")).strip()

SONARR_URL = os.getenv("SONARR_URL", "http://localhost:8989").rstrip("/")
SONARR_API_KEY = os.getenv("SONARR_API_KEY", os.getenv("HOMEPAGE_VAR_SONARR_API_KEY", "")).strip()

PROWLARR_URL = os.getenv("PROWLARR_URL", "http://localhost:9696").rstrip("/")
PROWLARR_API_KEY = os.getenv("PROWLARR_API_KEY", os.getenv("HOMEPAGE_VAR_PROWLARR_API_KEY", "")).strip()

QBITTORRENT_URL = os.getenv("QBITTORRENT_URL", "http://localhost:8080").rstrip("/")
QBITTORRENT_USER = os.getenv("QBITTORRENT_USER", "admin").strip()
QBITTORRENT_PASSWORD = os.getenv("QBITTORRENT_PASSWORD", os.getenv("HOMEPAGE_VAR_QBITTORRENT_PASSWORD", "adminadmin")).strip()

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "http://localhost:8096").rstrip("/")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY", os.getenv("HOMEPAGE_VAR_JELLYFIN_API_KEY", "")).strip()

JELLYSEERR_URL = os.getenv("JELLYSEERR_URL", "http://localhost:5055").rstrip("/")
JELLYSEERR_API_KEY = os.getenv("HOMEPAGE_VAR_JELLYSEERR_API_KEY") or os.getenv("JELLYSEERR_API_KEY", "")
JELLYSEERR_BOT_EMAIL = os.getenv("JELLYSEERR_BOT_EMAIL", "kewpie-bot@local.server")
JELLYSEERR_BOT_PASSWORD = os.getenv("JELLYSEERR_BOT_PASSWORD", "KewpiePassword123!").strip()

BAZARR_URL = os.getenv("BAZARR_URL", "http://localhost:6767").rstrip("/")
BAZARR_API_KEY = os.getenv("BAZARR_API_KEY", os.getenv("HOMEPAGE_VAR_BAZARR_API_KEY", "")).strip()

SABNZBD_URL = os.getenv("SABNZBD_URL", "http://localhost:8085").rstrip("/")
SABNZBD_API_KEY = os.getenv("SABNZBD_API_KEY", os.getenv("HOMEPAGE_VAR_SABNZBD_API_KEY", "")).strip()

# Monitored Storage Paths
MONITORED_PATHS = {
    "Root (OS)": "/",
    "Downloads": os.getenv("DOWNLOADS_PATH", "/home/mediaserver/Downloads"),
    "Movies": os.getenv("MOVIES_PATH", "/media/mediaserver/media/movies"),
    "TV Shows": os.getenv("TV_SHOWS_PATH", "/media/mediaserver/media/tv-series"),
    "Cold Movies": os.getenv("COLD_MOVIES_PATH", "/media/mediaserver/SAMSUNG/movies"),
    "Cold TV": os.getenv("COLD_TV_SHOWS_PATH", "/media/mediaserver/SAMSUNG/tv-series"),
}
