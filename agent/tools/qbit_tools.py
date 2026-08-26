import qbittorrentapi
from config import QBITTORRENT_URL, QBITTORRENT_USER, QBITTORRENT_PASSWORD

def _get_qbit_client():
    try:
        qbt_client = qbittorrentapi.Client(
            host=QBITTORRENT_URL,
            username=QBITTORRENT_USER,
            password=QBITTORRENT_PASSWORD,
            REQUESTS_ARGS={"timeout": 5}
        )
        qbt_client.auth_log_in()
        return qbt_client
    except Exception:
        return None

def get_torrent_downloads(limit: int = 10) -> list[dict]:
    """List active downloads and torrent statuses in qBittorrent."""
    client = _get_qbit_client()
    if not client:
        return [{"error": "Cannot connect to qBittorrent WebUI. Check credentials and URL."}]
    
    limit = min(max(1, limit), 20)
    try:
        torrents = client.torrents_info()[:limit]
        return [
            {
                "name": t.name,
                "hash": t.hash,
                "state": t.state,
                "progress_percent": round(t.progress * 100, 1),
                "dlspeed_mb": round(t.dlspeed / (1024 * 1024), 2),
                "upspeed_mb": round(t.upspeed / (1024 * 1024), 2),
                "num_seeds": t.num_seeds,
                "num_leechs": t.num_leechs,
                "eta_minutes": round(t.eta / 60, 1) if t.eta > 0 else "N/A"
            }
            for t in torrents
        ]
    except Exception as e:
        return [{"error": f"qBittorrent error: {str(e)}"}]

def control_torrent(torrent_hash: str, action: str) -> dict:
    """Pause, resume, or remove a stalled torrent by hash (action: 'pause', 'resume', 'delete_torrent_only')."""
    client = _get_qbit_client()
    if not client:
        return {"error": "Cannot connect to qBittorrent WebUI."}
    
    if action not in ["pause", "resume", "delete_torrent_only"]:
        return {"error": "Invalid action. Supported: 'pause', 'resume', 'delete_torrent_only'"}
    
    try:
        if action == "pause":
            client.torrents_pause(torrent_hashes=torrent_hash)
            return {"status": "success", "message": f"Paused torrent {torrent_hash}"}
        elif action == "resume":
            client.torrents_resume(torrent_hashes=torrent_hash)
            return {"status": "success", "message": f"Resumed torrent {torrent_hash}"}
        elif action == "delete_torrent_only":
            # Safety: delete_files=False to never delete existing media files on disk
            client.torrents_delete(delete_files=False, torrent_hashes=torrent_hash)
            return {"status": "success", "message": f"Removed torrent {torrent_hash} from queue (files preserved)."}
    except Exception as e:
        return {"error": f"Failed to perform {action} on torrent: {str(e)}"}
