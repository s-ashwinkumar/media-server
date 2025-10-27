# Updated Media Server Architecture

## Current Architecture (Simplified with Surfshark VPN)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MEDIA SERVER ARCHITECTURE                           │
│                         (Surfshark VPN Setup)                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SURFSHARK VPN TUNNEL                             │
│                         (All downloads protected)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER CONTAINERS                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ QBITTORRENT │  │   SONARR    │  │   RADARR    │  │  JELLYFIN   │      │
│  │  (Downloads)│  │ (TV Shows)  │  │  (Movies)   │  │(Media Server)│      │
│  │   Port:8080 │  │ Port:8989   │  │ Port:7878   │  │ Port:8096   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  JELLYSEERR │  │  PROWLARR   │  │   JACKETT   │  │FLARESOLVERR │      │
│  │ (Requests)  │  │ (Indexers)  │  │ (Indexers)  │  │ (Captcha)   │      │
│  │ Port:5055   │  │ Port:9696   │  │ Port:9117   │  │ Port:8191   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                   │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │        LOCAL STORAGE            │  │      EXTERNAL STORAGE           │  │
│  │                                 │  │                                 │  │
│  │  ┌─────────────┐ ┌─────────────┐│  │  ┌─────────────┐ ┌─────────────┐│  │
│  │  │   Configs   │ │ Downloads   ││  │  │ TV Shows    │ │   Movies    ││  │
│  │  │             │ │             ││  │  │             │ │             ││  │
│  │  │ • qBittorrent│ │ • radarr/   ││  │  │ • Organized │ │ • Organized ││  │
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
└─────────────────────────────────────────────────────────────────────────────┘

## Key Changes from Original Architecture:

### ✅ What's New/Updated:
1. **Surfshark VPN Integration**: All downloads go through VPN tunnel
2. **Separated Storage**: Local fast storage for downloads, external for media
3. **Single Compose File**: Simplified deployment with one docker-compose.yaml
4. **No NVIDIA Dependencies**: Removed GPU-specific configurations
5. **Streamlined Setup**: Focus on core functionality

### ❌ What's Removed:
1. **Multiple Compose Files**: No more nvidia, vpn-only variants
2. **NVIDIA GPU Support**: Removed from Jellyfin configuration
3. **Complex VPN Options**: Focused on Surfshark only
4. **Unified Storage**: No more single COMMON_PATH approach

### 🔄 Data Flow:
1. **Downloads**: qBittorrent → Local Storage (via VPN)
2. **Processing**: Sonarr/Radarr → Move to External Storage
3. **Streaming**: Jellyfin → External Storage (TV/Movies/Audio/Books)
4. **Requests**: Jellyseerr → Sonarr/Radarr → qBittorrent
5. **Indexing**: Prowlarr/Jackett → FlareSolverr (for captcha)

## Complete Port Configuration:

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
- **Jackett**: 9117 (Torrent proxy)
- **FlareSolverr**: 8191 (Captcha solver)

### **Service Connections (Internal):**
- **Jellyseerr → Jellyfin**: 7878
- **Jellyseerr → Radarr**: 7878  
- **Jellyseerr → Sonarr**: 8989
- **Radarr → qBittorrent**: 8080
- **Sonarr → qBittorrent**: 8080
- **Radarr → Jackett**: 9117
- **Sonarr → Jackett**: 9117
- **Radarr → Prowlarr**: 9696
- **Sonarr → Prowlarr**: 9696
- **Jackett → FlareSolverr**: 8191
- **Prowlarr → FlareSolverr**: 8191
