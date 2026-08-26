import requests
from config import PROWLARR_URL, PROWLARR_API_KEY

HEADERS = {
    "X-Api-Key": PROWLARR_API_KEY,
    "Content-Type": "application/json"
}

def _check_configured() -> bool:
    return bool(PROWLARR_URL and PROWLARR_API_KEY)

def prowlarr_check_indexer_health() -> dict:
    """Check health and status of all torrent and usenet indexers in Prowlarr."""
    if not _check_configured():
        return {"error": "Prowlarr is not configured or API key is missing."}
    try:
        indexers_resp = requests.get(f"{PROWLARR_URL}/api/v1/indexer", headers=HEADERS, timeout=10)
        indexers_resp.raise_for_status()
        indexers = indexers_resp.json()
        
        health_resp = requests.get(f"{PROWLARR_URL}/api/v1/health", headers=HEADERS, timeout=10)
        health_resp.raise_for_status()
        health_issues = health_resp.json()
        
        active_indexers = [i.get("name") for i in indexers if i.get("enable", False)]
        disabled_indexers = [i.get("name") for i in indexers if not i.get("enable", False)]
        
        issues = [
            {"source": h.get("source"), "type": h.get("type"), "message": h.get("message")}
            for h in health_issues
        ]
        
        return {
            "total_indexers": len(indexers),
            "active_indexers": active_indexers,
            "disabled_indexers": disabled_indexers,
            "health_issues": issues if issues else "All indexers healthy with no issues."
        }
    except Exception as e:
        return {"error": f"Failed to check Prowlarr indexers: {str(e)}"}

def prowlarr_sync_indexers() -> dict:
    """Trigger Prowlarr to sync indexers to Radarr and Sonarr."""
    if not _check_configured():
        return {"error": "Prowlarr is not configured."}
    try:
        resp = requests.post(f"{PROWLARR_URL}/api/v1/command", json={"name": "ApplicationSync"}, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return {"status": "success", "message": "Prowlarr application sync triggered successfully."}
    except Exception as e:
        return {"error": f"Failed to sync Prowlarr indexers: {str(e)}"}
