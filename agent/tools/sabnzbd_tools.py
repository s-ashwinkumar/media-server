import requests
from config import SABNZBD_URL, SABNZBD_API_KEY

def _check_configured() -> bool:
    return bool(SABNZBD_URL and SABNZBD_API_KEY)

def sabnzbd_get_queue(limit: int = 5) -> dict:
    """Get active Usenet downloads, download speeds, and queue status in SABnzbd."""
    if not _check_configured():
        return {"error": "SABnzbd is not configured or API key is missing."}
    limit = min(max(1, limit), 10)
    try:
        resp = requests.get(
            f"{SABNZBD_URL}/api",
            params={"mode": "queue", "output": "json", "apikey": SABNZBD_API_KEY},
            timeout=10
        )
        resp.raise_for_status()
        q = resp.json().get("queue", {})
        
        slots = q.get("slots", [])[:limit]
        items = [
            {
                "filename": s.get("filename"),
                "size_mb": s.get("size"),
                "sizeleft_mb": s.get("sizeleft"),
                "percentage": s.get("percentage"),
                "status": s.get("status"),
                "timeleft": s.get("timeleft")
            }
            for s in slots
        ]
        
        return {
            "speed": q.get("speed", "0 B/s"),
            "status": q.get("status", "Idle"),
            "timeleft": q.get("timeleft", "0:00:00"),
            "sizeleft_mb": q.get("sizeleft", "0 MB"),
            "active_downloads": items if items else "Queue is empty."
        }
    except Exception as e:
        return {"error": f"Failed to get SABnzbd queue: {str(e)}"}

def sabnzbd_control(action: str) -> dict:
    """Pause or resume the SABnzbd download queue (action: 'pause' or 'resume')."""
    if not _check_configured():
        return {"error": "SABnzbd is not configured."}
    if action not in ["pause", "resume"]:
        return {"error": "Action must be 'pause' or 'resume'."}
    try:
        resp = requests.get(
            f"{SABNZBD_URL}/api",
            params={"mode": action, "output": "json", "apikey": SABNZBD_API_KEY},
            timeout=10
        )
        resp.raise_for_status()
        return {"status": "success", "message": f"SABnzbd queue {action}d successfully."}
    except Exception as e:
        return {"error": f"Failed to {action} SABnzbd queue: {str(e)}"}
