# Updated Media Server Architecture

## Current Architecture (Simplified with Surfshark VPN)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        JELLYFLIX  ARCHITECTURE                             │
│                         (Surfshark VPN Setup)                              │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLIENT ACCESS (LAN / TAILSCALE)                     │
│                                                                             │
│  Browser ── DNS resolves *.kewpie.top ──► Traefik (port 80) ──► Services    │
│            (Cloudflare wildcard to TS IP, or /etc/hosts on LAN)             │
│                                                                             │
│  Examples: http://sonarr.kewpie.top, http://jellyfin.kewpie.top             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SURFSHARK VPN TUNNEL                              │
│                         (All downloads protected)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER CONTAINERS                               │
│  ┌───────────────┐                                                         │
│  │   TRAEFIK     │  Reverse proxy for all WebUIs                           │
│  │   Port:80     │  (subdomains via labels, e.g. sonarr.kewpie.top)        │
│  │ Dashboard:8083│                                                         │
│  └───────────────┘                                                         │
│                                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ QBITTORRENT │  │   SONARR    │  │   RADARR    │  │  JELLYFIN   │        │
│  │ (Downloads) │  │ (TV Shows)  │  │  (Movies)   │  │(MediaServer)│        │
│  │ (via VPN ns)│  │ Port:8989   │  │ Port:7878   │  │ Port:8096   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  JELLYSEERR │  │  PROWLARR   │  │FLARESOLVERR │  │  HOMEPAGE   │        │
│  │ (Requests)  │  │ (Indexers)  │  │ (Captcha)   │  │ (Dashboard) │        │
│  │ Port:5055   │  │ Port:9696   │  │ Port:8191   │  │ Port:3000   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   BAZARR    │  │   SABNZBD   │  │ FILEBROWSER │                         │
│  │ (Subtitles) │  │ (Usenet)    │  │ (File UI)   │                         │
│  │ Port:6767   │  │ Port:8080   │  │ Port:80     │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                   │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │        LOCAL STORAGE            │  │      EXTERNAL STORAGE           │  │
│  │                                 │  │                                 │  │
│  │  ┌─────────────┐ ┌─────────────┐│  │  ┌─────────────┐ ┌─────────────┐│  │
│  │  │   Configs   │ │ Downloads   ││  │  │ TV Shows    │ │   Movies    ││  │
│  │  │             │ │             ││  │  │             │ │             ││  │
│  │  │ • qBittorent│ │ • radarr/   ││  │  │ • Organized │ │ • Organized ││  │
│  │  │ • Sonarr    │ │ • sonarr/   ││  │  │ • Final     │ │ • Final     ││  │
│  │  │ • Radarr    │ │ • completed ││  │  │   Storage   │ │   Storage   ││  │
│  │  │ • Jellyfin  │ │             ││  │  │             │ │             ││  │
│  │  │ • etc.      │ │             ││  │  │             │ │             ││  │
│  │  └─────────────┘ └─────────────┘│  │  └─────────────┘ └─────────────┘│  │
│  │                                 │  │                                 │  │
│  │  ┌─────────────┐                │  │  ┌─────────────┐ ┌─────────────┐│  │
│  │  │   Cache     │                │  │  │   Audio     │ │   Books     ││  │
│  │  │             │                │  │  │             │ │             ││  │
│  │  │ • Jellyfin  │                │  │  │ • Music     │ │ • E-books   ││  │
│  │  │   cache     │                │  │  │ • Podcasts  │ │ • Audiobooks││  │
│  │  └─────────────┘                │  │  └─────────────┘ └─────────────┘│  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘

### 🔄 Data Flow:
1. **Downloads**: qBittorrent → Local Storage (via VPN)
2. **Processing**: Sonarr/Radarr → Move to External Storage
3. **Streaming**: Jellyfin → External Storage (TV/Movies/Audio/Books)
4. **Requests**: Jellyseerr → Sonarr/Radarr → qBittorrent
5. **Indexing**: Prowlarr → FlareSolverr (for captcha)

## Complete Port Configuration:

### **Reverse Proxy / Dashboard**
- **Traefik**: 80 (HTTP entrypoint for all subdomains)
- **Traefik Dashboard**: 8083

### **VPN & Download Services:**
- **Surfshark VPN (GlueTun)**: 8080 (VPN tunnel)
- **qBittorrent**: 8080 (through VPN tunnel, no direct access)

### **Media Management Services:**
- **Sonarr**: 8989 (TV Show automation)
- **Radarr**: 7878 (Movie automation)
- **Jellyfin**: 8096 (HTTP), 8920 (HTTPS), 7359/UDP (DLNA), 1900/UDP (SSDP)
- **Jellyseerr**: 5055 (Media requests)

### **Indexer Services:**
- **Prowlarr**: 9696 (Indexer manager)
- **FlareSolverr**: 8191 (Captcha solver)

### **Utility Services:**
- **Homepage**: 3000 (dashboard)
- **Bazarr**: 6767 (subtitles)
- **SABnzbd**: 8080 (container port; host may map differently)
- **Filebrowser**: 80 (container port; host may map differently)

### **Service Connections (Internal):**
- **Jellyseerr → Jellyfin**: 7878
- **Jellyseerr → Radarr**: 7878  
- **Jellyseerr → Sonarr**: 8989
- **Radarr → qBittorrent**: 8080
- **Sonarr → qBittorrent**: 8080
- **Radarr → Prowlarr**: 9696
- **Sonarr → Prowlarr**: 9696
- **Prowlarr → FlareSolverr**: 8191
