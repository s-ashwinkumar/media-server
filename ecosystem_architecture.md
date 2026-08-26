# Media Server Ecosystem: Current Setup vs. nzb360 vs. JellyWatch

This document visualizes how **nzb360** and **JellyWatch** layer on top of your existing Docker media stack.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Clients["Clients & Control Layer"]
        NZB["<b>nzb360 (Android App)</b><br/>• Arr Stack Management<br/>• Download Queues & Indexers<br/>• Jellyseerr Request Approvals"]
        JWM["<b>JellyWatch Mobile (Android)</b><br/>• Active Stream Telemetry<br/>• Transcode & Codec Monitoring<br/>• Remote Session Management"]
        JWTV["<b>JellyWatch TV (Android/Google TV)</b><br/>• High-Bitrate 4K / HDR / DV Player<br/>• Dual mpv & ExoPlayer Engines<br/>• Audio Passthrough (TrueHD / DTS:X)"]
        HP["<b>Homepage (Web Browser)</b><br/>• Central Desktop Web Dashboard"]
    end

    subgraph Server["Your Media Server Stack (Docker)"]
        Traefik["<b>Traefik</b> (:80 / :8083)<br/>Reverse Proxy & Subdomains"]
        Jellyfin["<b>Jellyfin</b> (:8096)<br/>Media Library & Transcoder"]
        Arrs["<b>*Arr Apps</b><br/>Sonarr / Radarr / Bazarr / Prowlarr"]
        Downloaders["<b>Download Clients</b><br/>qBittorrent (VPN) & SABnzbd"]
        Jellyseerr["<b>Jellyseerr</b> (:5055)<br/>Media Requests & Discovery"]
    end

    NZB -->|"API over Traefik / LAN"| Arrs
    NZB -->|"API over Traefik / LAN"| Downloaders
    NZB -->|"API over Traefik / LAN"| Jellyseerr
    JWM -->|"API over Traefik / LAN"| Jellyfin
    JWTV -->|"Direct Stream (LAN / Tailscale)"| Jellyfin
    HP -->|"Widgets & Dashboard Links"| Traefik
    Jellyseerr -->|"Pushes requests"| Arrs
    Arrs -->|"Sends grabs"| Downloaders
```

---

## Layer Breakdown

| Layer | Component | Primary Use Case |
| :--- | :--- | :--- |
| **Media Playback** | JellyWatch TV / Official Jellyfin App | Watching media on TVs and streaming devices |
| **Server Telemetry** | JellyWatch Mobile / Jellyfin Admin / Jellystat | Monitoring who is watching, transcoding reasons, and bandwidth |
| **Download Automation** | nzb360 (Mobile) / Arr Web UIs | Triggering manual downloads, monitoring queues, approving requests |
| **Web Dashboard** | Homepage | Desktop-friendly launcher and status dashboard |
| **Infrastructure** | Docker Compose + Traefik | Host services, storage volumes, and reverse proxy routing |
