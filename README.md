# Jellyflix Media Server

Docker Compose stack for a self-hosted media server: Jellyfin, *arr apps, qBittorrent over Surfshark VPN (Gluetun), Traefik subdomain routing, and Homepage dashboard.

## Services

| Service | Role |
|---------|------|
| [Jellyfin](https://jellyfin.org/) | Media streaming |
| [Seerr](https://github.com/seerr-team/seerr) | Media requests (Jellyseerr) |
| [Sonarr](https://sonarr.tv/) / [Radarr](https://radarr.video/) | TV / movie automation |
| [Prowlarr](https://github.com/Prowlarr/Prowlarr) | Indexer manager |
| [qBittorrent](https://www.qbittorrent.org/) | Torrent client (routed through VPN) |
| [Gluetun](https://github.com/qdm12/gluetun) | Surfshark OpenVPN tunnel |
| [SABnzbd](https://sabnzbd.org/) | Usenet downloads |
| [Bazarr](https://www.bazarr.media/) | Subtitles |
| [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | Cloudflare bypass for indexers |
| [Traefik](https://traefik.io/) | Reverse proxy (`*.your-domain`) |
| [Homepage](https://gethomepage.dev/) | Dashboard |
| [Filebrowser](https://filebrowser.org/) | Web file manager |

See [architecture.md](architecture.md) for routing, storage layout, and port reference.

## Prerequisites

- Docker Engine + Docker Compose
- Surfshark account with [OpenVPN service credentials](https://support.surfshark.com/hc/en-us/articles/360013538779) (not your login email/password)
- Storage paths for configs, downloads, and media (see `.env.example`)

## Setup

```bash
git clone https://github.com/s-ashwinkumar/media-server.git
cd media-server
cp compose_files/.env.example compose_files/.env
```

Edit `compose_files/.env`:

- **VPN:** `OPENVPN_USER`, `OPENVPN_PASSWORD`, `SERVER_COUNTRIES`, `SERVER_HOSTNAMES`
- **Paths:** `CONFIGS_PATH`, `DOWNLOADS_PATH`, `TV_SHOWS_PATH`, `MOVIES_PATH`, cold storage paths, etc.
- **Routing:** `TRAEFIK_DOMAIN` (e.g. `kewpie.top`)
- **Homepage widgets (optional):** `HOMEPAGE_VAR_*` API keys

Start the stack:

```bash
cd compose_files
docker compose up -d
```

Verify VPN (should show a non-home IP):

```bash
docker exec qbittorrent curl -s https://api.ipify.org/
```

## Access

Services are reached via Traefik subdomains. Set `TRAEFIK_DOMAIN` in `.env`, then use:

| Service | URL |
|---------|-----|
| Jellyfin | `http://jellyfin.<domain>` |
| Jellyseerr | `http://jellyseerr.<domain>` |
| Sonarr | `http://sonarr.<domain>` |
| Radarr | `http://radarr.<domain>` |
| Prowlarr | `http://prowlarr.<domain>` |
| qBittorrent | `http://qbittorrent.<domain>` |
| Bazarr | `http://bazarr.<domain>` |
| SABnzbd | `http://sabnzbd.<domain>` |
| Homepage | `http://homepage.<domain>` |
| Filebrowser | `http://filebrowser.<domain>` |
| Traefik dashboard | `http://traefik.<domain>` or `http://<server-ip>:8083` |

**DNS:** Traefik routes by hostname, but something must resolve each subdomain to your server IP.

- **LAN:** `/etc/hosts` entries (one line per subdomain; wildcards are not supported)
- **Tailscale / remote:** DNS wildcard (`*.your-domain`) pointing to the server's Tailscale IP, or Tailscale split DNS

Direct port access still works as a fallback (e.g. `http://<server-ip>:8989` for Sonarr).

## Homepage config

Version-controlled config lives in `homepage/`. The container reads from `${CONFIGS_PATH}/homepage` (symlink or copy the repo folder there).

After changes:

```bash
cd compose_files
docker compose up -d homepage
```

## Storage

Paths are set in `.env`, not `docker-compose.yaml`. See `.env.example` for the layout:

- **Local:** configs, downloads, Jellyfin cache
- **Media drive:** active TV/movies (`TV_SHOWS_PATH`, `MOVIES_PATH`)
- **Cold storage:** archive media on secondary drive (`COLD_*`, `BOOKS_PATH`)

For stable drive mount points after reboot, see:

- `compose_files/docs/media-drive-fstab-setup.md`
- `compose_files/docs/samsung-drive-fstab-setup.md`

## Web UI setup

Service integration (qBittorrent, Radarr, Sonarr, Prowlarr, Jellyfin, Jellyseerr): `docs/WEB_UI_CONFIGURATION_GUIDE.md`

## Updates

```bash
cd compose_files
docker compose pull
docker compose up -d
```

Optional cleanup of old images: `docker image prune`
