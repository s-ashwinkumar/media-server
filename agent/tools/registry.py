import json
from tools.radarr_tools import (
    radarr_search_movie,
    radarr_get_releases,
    radarr_trigger_search,
    radarr_refresh_movie,
    radarr_add_movie,
    radarr_delete_movie,
    radarr_grab_release,
    radarr_get_queue
)
from tools.sonarr_tools import (
    sonarr_search_series,
    sonarr_get_episodes,
    sonarr_trigger_search,
    sonarr_refresh_series,
    sonarr_add_series,
    sonarr_delete_series,
    sonarr_get_releases,
    sonarr_grab_release,
    sonarr_get_queue
)
from tools.docker_tools import (
    list_docker_containers,
    restart_docker_container,
    get_docker_container_logs
)
from tools.qbit_tools import (
    get_torrent_downloads,
    control_torrent
)
from tools.system_tools import (
    get_disk_space,
    get_system_stats
)
from tools.jellyseerr_tools import (
    jellyseerr_list_requests,
    jellyseerr_request_media,
    jellyseerr_approve_request,
    jellyseerr_decline_request
)
from tools.jellyfin_tools import (
    jellyfin_get_active_streams,
    jellyfin_scan_library
)
from tools.vpn_tools import (
    check_vpn_ip_leak
)
from tools.prowlarr_tools import (
    prowlarr_check_indexer_health,
    prowlarr_sync_indexers
)
from tools.bazarr_tools import (
    bazarr_get_missing_subtitles
)
from tools.sabnzbd_tools import (
    sabnzbd_get_queue,
    sabnzbd_control
)

TOOLS_SCHEMA = [
    # --- Radarr Tools ---
    {
        "type": "function",
        "function": {
            "name": "radarr_search_movie",
            "description": "Search for a movie in the Radarr library or search indexers for new movies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The movie title to search for."},
                    "limit": {"type": "integer", "description": "Maximum results to return (max 5).", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_trigger_search",
            "description": "Trigger Radarr's automatic indexer search to find and download missing movie(s).",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of Radarr movie IDs."}
                },
                "required": ["movie_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_get_releases",
            "description": "Search indexers for available releases/torrents for a specific movie in Radarr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer", "description": "The internal Radarr movie ID."},
                    "limit": {"type": "integer", "description": "Max releases to return (max 5).", "default": 5}
                },
                "required": ["movie_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_grab_release",
            "description": "Grab a specific release and send it to the download client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guid": {"type": "string", "description": "The release GUID."},
                    "indexer_id": {"type": "integer", "description": "The indexer ID."}
                },
                "required": ["guid", "indexer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_get_queue",
            "description": "Get active Radarr downloads in progress.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 5}}
            }
        }
    },
    # --- Sonarr Tools ---
    {
        "type": "function",
        "function": {
            "name": "sonarr_search_series",
            "description": "Search for a TV series in Sonarr library or look up new series.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The TV series title."},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_get_episodes",
            "description": "Get episode list for a TV series in Sonarr to find which episodes are missing or downloaded.",
            "parameters": {
                "type": "object",
                "properties": {
                    "series_id": {"type": "integer", "description": "The Sonarr series ID."},
                    "missing_only": {"type": "boolean", "description": "Filter to missing episodes only.", "default": True}
                },
                "required": ["series_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_trigger_search",
            "description": "Trigger Sonarr's automatic search for missing episode IDs or an entire series.",
            "parameters": {
                "type": "object",
                "properties": {
                    "episode_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of Sonarr episode IDs."},
                    "series_id": {"type": "integer", "description": "Optional series ID."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_get_releases",
            "description": "Search indexers for available releases for a specific Sonarr episode ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "episode_id": {"type": "integer", "description": "The Sonarr episode ID."},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["episode_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_grab_release",
            "description": "Grab a specific Sonarr release and send it to download client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guid": {"type": "string", "description": "The release GUID."},
                    "indexer_id": {"type": "integer", "description": "The indexer ID."}
                },
                "required": ["guid", "indexer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_get_queue",
            "description": "Get active Sonarr episode downloads in progress.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 5}}
            }
        }
    },
    # --- Jellyfin Tools ---
    {
        "type": "function",
        "function": {
            "name": "jellyfin_get_active_streams",
            "description": "See who is currently watching on Jellyfin, titles, and whether it's DirectPlay or Transcoding.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "jellyfin_scan_library",
            "description": "Trigger an immediate Jellyfin library refresh / scan.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    # --- Jellyseerr Tools ---
    {
        "type": "function",
        "function": {
            "name": "jellyseerr_list_requests",
            "description": "List pending or approved media requests submitted in Jellyseerr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "approved", "all"], "default": "pending"},
                    "limit": {"type": "integer", "default": 5}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "jellyseerr_request_media",
            "description": "Submit a new movie or TV show request to the Jellyseerr approval queue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the movie or TV show to request."},
                    "media_type": {"type": "string", "enum": ["movie", "tv"], "description": "Whether it's a movie or tv series.", "default": "movie"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "jellyseerr_approve_request",
            "description": "Approve a pending media request in Jellyseerr.",
            "parameters": {
                "type": "object",
                "properties": {"request_id": {"type": "integer", "description": "The request ID."}},
                "required": ["request_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "jellyseerr_decline_request",
            "description": "Decline a pending media request in Jellyseerr.",
            "parameters": {
                "type": "object",
                "properties": {"request_id": {"type": "integer", "description": "The request ID."}},
                "required": ["request_id"]
            }
        }
    },
    # --- VPN Privacy & Prowlarr ---
    {
        "type": "function",
        "function": {
            "name": "check_vpn_ip_leak",
            "description": "Check public IP address and ISP of torrent VPN to verify no IP leaks.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prowlarr_check_indexer_health",
            "description": "Check health of indexers in Prowlarr to see if any are failing or disabled.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prowlarr_sync_indexers",
            "description": "Sync working indexers from Prowlarr to Radarr and Sonarr.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    # --- Subtitles (Bazarr) & Usenet (SABnzbd) ---
    {
        "type": "function",
        "function": {
            "name": "bazarr_get_missing_subtitles",
            "description": "List movies and TV episodes currently missing subtitles in Bazarr.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 5}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sabnzbd_get_queue",
            "description": "Get active Usenet downloads and speeds in SABnzbd.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 5}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sabnzbd_control",
            "description": "Pause or resume the SABnzbd Usenet download queue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["pause", "resume"], "description": "Action to perform."}
                },
                "required": ["action"]
            }
        }
    },
    # --- Torrent & Container & Host ---
    {
        "type": "function",
        "function": {
            "name": "get_torrent_downloads",
            "description": "Get active qBittorrent torrents, download speeds, progress, and seed counts.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_torrent",
            "description": "Pause, resume, or remove a stalled torrent by hash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "torrent_hash": {"type": "string", "description": "The torrent hash."},
                    "action": {"type": "string", "enum": ["pause", "resume", "delete_torrent_only"]}
                },
                "required": ["torrent_hash", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_docker_containers",
            "description": "List all Docker containers and health status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_docker_container",
            "description": "Restart a specific Docker container safely by name.",
            "parameters": {
                "type": "object",
                "properties": {"container_name": {"type": "string"}},
                "required": ["container_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_docker_container_logs",
            "description": "Fetch latest logs from a container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string"},
                    "lines": {"type": "integer", "default": 30}
                },
                "required": ["container_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_disk_space",
            "description": "Check free disk space on storage pools.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": "Check server CPU usage, memory, and hardware temperatures.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_refresh_series",
            "description": "Rescan disk and refresh series metadata in Sonarr.",
            "parameters": {
                "type": "object",
                "properties": {"series_id": {"type": "integer", "description": "The Sonarr series ID."}},
                "required": ["series_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_refresh_movie",
            "description": "Rescan disk and refresh movie metadata in Radarr.",
            "parameters": {
                "type": "object",
                "properties": {"movie_id": {"type": "integer", "description": "The Radarr movie ID."}},
                "required": ["movie_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_delete_movie",
            "description": "Delete a movie and its media files from Radarr and disk (Admin only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer", "description": "The Radarr movie ID."},
                    "delete_files": {"type": "boolean", "description": "Whether to delete files from disk.", "default": True}
                },
                "required": ["movie_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_add_series",
            "description": "Add a new TV series to Sonarr library and optionally search for missing episodes (Admin only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "tvdb_id": {"type": "integer", "description": "The TVDB ID of the series."},
                    "query": {"type": "string", "description": "Title or IMDb ID (e.g. imdb:tt12345) if tvdb_id unknown."},
                    "seasons_to_monitor": {"type": "array", "items": {"type": "integer"}, "description": "List of season numbers to monitor, e.g. [3] for season 3 only. Omit for all seasons."},
                    "search_missing": {"type": "boolean", "description": "Whether to immediately search indexers for missing episodes.", "default": True}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "radarr_add_movie",
            "description": "Add a new movie to Radarr library and search indexers (Admin only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "tmdb_id": {"type": "integer", "description": "The TMDB ID of the movie."},
                    "query": {"type": "string", "description": "Title or IMDb ID if tmdb_id unknown."},
                    "search_now": {"type": "boolean", "description": "Whether to immediately search indexers.", "default": True}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sonarr_delete_series",
            "description": "Delete a TV series and its media files from Sonarr and disk (Admin only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "series_id": {"type": "integer", "description": "The Sonarr series ID."},
                    "delete_files": {"type": "boolean", "description": "Whether to delete files from disk.", "default": True}
                },
                "required": ["series_id"]
            }
        }
    }
]

# Read-only tools and request tools for non-admin users
USER_ALLOWED_TOOLS = {
    "radarr_search_movie",
    "sonarr_search_series",
    "sonarr_get_episodes",
    "jellyfin_get_active_streams",
    "jellyseerr_request_media"
}

TOOL_DISPATCHER = {
    "radarr_search_movie": radarr_search_movie,
    "radarr_trigger_search": radarr_trigger_search,
    "radarr_refresh_movie": radarr_refresh_movie,
    "radarr_add_movie": radarr_add_movie,
    "radarr_delete_movie": radarr_delete_movie,
    "radarr_get_releases": radarr_get_releases,
    "radarr_grab_release": radarr_grab_release,
    "radarr_get_queue": radarr_get_queue,
    "sonarr_search_series": sonarr_search_series,
    "sonarr_get_episodes": sonarr_get_episodes,
    "sonarr_trigger_search": sonarr_trigger_search,
    "sonarr_refresh_series": sonarr_refresh_series,
    "sonarr_add_series": sonarr_add_series,
    "sonarr_delete_series": sonarr_delete_series,
    "sonarr_get_releases": sonarr_get_releases,
    "sonarr_grab_release": sonarr_grab_release,
    "sonarr_get_queue": sonarr_get_queue,
    "jellyfin_get_active_streams": jellyfin_get_active_streams,
    "jellyfin_scan_library": jellyfin_scan_library,
    "jellyseerr_list_requests": jellyseerr_list_requests,
    "jellyseerr_request_media": jellyseerr_request_media,
    "jellyseerr_approve_request": jellyseerr_approve_request,
    "jellyseerr_decline_request": jellyseerr_decline_request,
    "check_vpn_ip_leak": check_vpn_ip_leak,
    "prowlarr_check_indexer_health": prowlarr_check_indexer_health,
    "prowlarr_sync_indexers": prowlarr_sync_indexers,
    "bazarr_get_missing_subtitles": bazarr_get_missing_subtitles,
    "sabnzbd_get_queue": sabnzbd_get_queue,
    "sabnzbd_control": sabnzbd_control,
    "get_torrent_downloads": get_torrent_downloads,
    "control_torrent": control_torrent,
    "list_docker_containers": list_docker_containers,
    "restart_docker_container": restart_docker_container,
    "get_docker_container_logs": get_docker_container_logs,
    "get_disk_space": get_disk_space,
    "get_system_stats": get_system_stats,
}

def get_tools_schema_for_user(is_admin: bool) -> list[dict]:
    """Return tool schemas based on user role."""
    if is_admin:
        return TOOLS_SCHEMA
    return [t for t in TOOLS_SCHEMA if t["function"]["name"] in USER_ALLOWED_TOOLS]

def execute_tool(name: str, arguments: dict, is_admin: bool = False) -> str:
    """Safely execute a tool with role authorization checks."""
    if not is_admin and name not in USER_ALLOWED_TOOLS:
        return json.dumps({"error": f"Permission denied: Action '{name}' is restricted to administrators."})

    func = TOOL_DISPATCHER.get(name)
    if not func:
        return json.dumps({"error": f"Tool '{name}' not found."})
    try:
        if name == "jellyseerr_request_media":
            arguments["is_admin"] = is_admin
        res = func(**arguments)
        return json.dumps(res)
    except Exception as e:
        return json.dumps({"error": f"Error executing '{name}': {str(e)}"})
