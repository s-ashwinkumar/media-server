# Web UI Configuration Guide (Optional)

This document contains the detailed, step-by-step configuration notes for the various service web interfaces.

It was split out of the main `README.md` to keep the README focused on install + operations.

---

## qBittorrent

1. Open the WebUI.
2. Log in with the default credentials:
   - **Username**: `admin`
   - **Password**: `adminadmin`

<div style="text-align: center">
    <img src="../image/qBittorrent/qbit1.png" style="margin: 15px 10px;">
</div>

   *Note: The default credentials may have changed. In many cases, qBittorrent generates a temporary password on first start. To view it: `docker logs qbittorrent`*

3. Go to **Options** → **Downloads** and configure:
   - **Default Torrent Management Mode**: `Automatic`
   - **When Torrent Category changed**: `Relocate torrent`
   - **When Default Save Path changed**: `Relocate affected torrents`
   - **When Category Save Path changed**: `Relocate affected torrents`
   - **Default Save Path**: `/downloads`

<div style="text-align: center">
    <img src="../image/qBittorrent/qbit2.png" style="margin: 15px 10px;">
</div>

### Category Configuration

Create categories matching Radarr/Sonarr:
- **radarr** → `/downloads/radarr`
- **sonarr** → `/downloads/sonarr`

<div style="text-align: center">
    <img src="../image/qBittorrent/qbit3.png" style="margin: 15px 10px;">
</div>

---

## Radarr

### Media Management

1. **Settings** → **Media Management**
2. **Add Root Folder**: `/movies` (or your configured movies path)
3. Enable **Use Hardlinks instead of Copy** (Advanced → Importing)

<div style="text-align: center">
    <img src="../image/radarr/rad3.png" style="margin: 15px 10px;">
</div>

### Download Clients

1. **Settings** → **Download Clients** → **+** → **qBittorrent**
2. Example:
   - **Host**: `qbittorrent`
   - **Username**: `admin`
   - **Password**: `adminadmin`
   - **Category**: `radarr`

> If `qbittorrent` as host doesn’t work in your environment, try the server IP (e.g. `192.168.x.x`).

<div style="text-align: center">
    <img src="../image/radarr/rad5.png" style="margin: 15px 10px;">
</div>

### Indexer (Optional)

Configure a Torznab indexer as desired.

---

## Sonarr

### Media Management

1. **Settings** → **Media Management**
2. **Add Root Folder**: `/tv-shows` (or your configured TV shows path)
3. Enable **Use Hardlinks instead of Copy** (Advanced → Importing)

<div style="text-align: center">
    <img src="../image/sonarr/son1.png" style="margin: 15px 10px;">
</div>

### Download Clients

1. **Settings** → **Download Clients** → **+** → **qBittorrent**
2. Example:
   - **Host**: `qbittorrent`
   - **Username**: `admin`
   - **Password**: `adminadmin`
   - **Category**: `sonarr`

<div style="text-align: center">
    <img src="../image/sonarr/son2.png" style="margin: 15px 10px;">
</div>

### Indexer (Optional)

Configure a Torznab indexer as desired.

---

## Prowlarr

### Configure Torrent Indexers

Add any indexers you want under **Indexers**.

<div style="text-align: center">
    <img src="../image/prowlarr/pro1.png" style="margin: 15px 10px;">
</div>

### Configure FlareSolverr

- **Host**: `http://flaresolverr:8191/`

### Configure Apps (Radarr/Sonarr)

- **Radarr Server**: `http://radarr:7878`
- **Sonarr Server**: `http://sonarr:8989`

<div style="text-align: center">
    <img src="../image/prowlarr/pro2.png" style="margin: 15px 10px;">
    <img src="../image/prowlarr/pro3.png" style="margin: 15px 10px;">
</div>

---

## Jellyfin

### Initial Setup

Add your libraries (Movies/Shows/etc.) pointing at the mounted paths inside the container.

### Adding Users

Create additional user accounts as needed under **Users**.

---

## Jellyseerr

### Sign In / Configuration

Use your Jellyfin account and point Jellyseerr at:
- **Jellyfin URL**: `http://jellyfin:8096/`

### Integrating with Radarr / Sonarr

Add Radarr and Sonarr servers with:
- **Radarr**: `http://radarr:7878`
- **Sonarr**: `http://sonarr:8989`

