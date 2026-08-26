import requests
from config import JELLYSEERR_URL, JELLYSEERR_API_KEY, JELLYSEERR_BOT_EMAIL, JELLYSEERR_BOT_PASSWORD

HEADERS = {
    "X-Api-Key": JELLYSEERR_API_KEY,
    "Content-Type": "application/json"
}

_bot_session = None

def _get_bot_session() -> requests.Session:
    """Get or create an authenticated Jellyseerr user session for Kewpie (non-admin)."""
    global _bot_session
    if _bot_session is not None:
        return _bot_session
    
    session = requests.Session()
    try:
        login_resp = session.post(
            f"{JELLYSEERR_URL}/api/v1/auth/local",
            json={"email": JELLYSEERR_BOT_EMAIL, "password": JELLYSEERR_BOT_PASSWORD},
            timeout=10
        )
        if login_resp.ok:
            _bot_session = session
            return _bot_session
    except Exception:
        pass
    return None

def _check_configured() -> bool:
    return bool(JELLYSEERR_URL and JELLYSEERR_API_KEY)

def jellyseerr_list_requests(status: str = "pending", limit: int = 5) -> list[dict]:
    """List media requests in Jellyseerr/Overseerr (status: 'pending', 'approved', 'all')."""
    if not _check_configured():
        return [{"error": "Jellyseerr is not configured or API key is missing."}]
    
    limit = min(max(1, limit), 10)
    filter_val = "pending" if status == "pending" else "all"
    try:
        resp = requests.get(
            f"{JELLYSEERR_URL}/api/v1/request",
            params={"take": limit, "filter": filter_val, "sort": "added"},
            headers=HEADERS,
            timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        output = []
        for r in results:
            media = r.get("media", {})
            req_by = r.get("requestedBy", {}).get("displayName", "Unknown")
            title = media.get("title") or media.get("name") or "Unknown Title"
            output.append({
                "requestId": r.get("id"),
                "status": r.get("status"),  # 1 = pending, 2 = approved, 3 = declined
                "mediaType": r.get("type"),
                "title": title,
                "requestedBy": req_by,
                "createdAt": r.get("createdAt", "")[:10]
            })
        return output if output else [{"message": "No requests found matching criteria."}]
    except Exception as e:
        return [{"error": f"Failed to list Jellyseerr requests: {str(e)}"}]

def jellyseerr_request_media(title: str, media_type: str = "movie", is_admin: bool = False, force_approve: bool = False) -> dict:
    """
    Search and submit media requests directly to Jellyseerr.
    - If requested by non-admin: Submits via kewpie-bot user session so it enters Jellyseerr as 'Pending Approval' (status: 1).
    - If requested by admin: Submits via Admin API key (auto-approved and queued for download).
    """
    if not _check_configured():
        return {"error": "Jellyseerr is not configured."}
    try:
        # Search for TMDB/TVDB ID
        search_resp = requests.get(f"{JELLYSEERR_URL}/api/v1/search", params={"query": title}, headers=HEADERS, timeout=10)
        search_resp.raise_for_status()
        results = search_resp.json().get("results", [])
        
        if not results:
            return {"error": f"Could not find any movie or TV show matching '{title}'."}
        
        matched = None
        for r in results:
            if media_type.lower() in ["tv", "show", "series"] and r.get("mediaType") == "tv":
                matched = r
                break
            elif media_type.lower() in ["movie", "film"] and r.get("mediaType") == "movie":
                matched = r
                break
        if not matched:
            matched = results[0]
            
        media_id = matched.get("id")
        actual_type = matched.get("mediaType", "movie")
        media_title = matched.get("title") or matched.get("name") or title
        year = matched.get("releaseDate", "")[:4] or matched.get("firstAirDate", "")[:4]

        payload = {
            "mediaId": media_id,
            "mediaType": actual_type
        }
        if actual_type == "tv":
            payload["seasons"] = "all"

        # If non-admin and not force_approved by admin, submit through the kewpie-bot session
        if not is_admin and not force_approve:
            bot_session = _get_bot_session()
            if bot_session:
                req_resp = bot_session.post(f"{JELLYSEERR_URL}/api/v1/request", json=payload, timeout=15)
                req_resp.raise_for_status()
                req_data = req_resp.json()
                req_id = req_data.get("id")
                return {
                    "status": "pending_approval",
                    "requestId": req_id,
                    "title": media_title,
                    "year": year,
                    "mediaType": actual_type,
                    "message": f"Submitted request for **{media_title}** (#{req_id}) into Jellyseerr. It is **Pending Approval** by an administrator."
                }

        # Admin request or Admin approved -> Submit via Admin API key (auto-approved)
        req_resp = requests.post(f"{JELLYSEERR_URL}/api/v1/request", json=payload, headers=HEADERS, timeout=15)
        req_resp.raise_for_status()
        req_data = req_resp.json()
        req_id = req_data.get("id")
        
        return {
            "status": "success",
            "requestId": req_id,
            "title": media_title,
            "year": year,
            "mediaType": actual_type,
            "message": f"Successfully approved and queued **{media_title}** (#{req_id}) for download!"
        }
    except Exception as e:
        return {"error": f"Failed to submit Jellyseerr request: {str(e)}"}

def jellyseerr_approve_request(request_id: int) -> dict:
    """Approve a pending media request in Jellyseerr."""
    if not _check_configured():
        return {"error": "Jellyseerr is not configured."}
    try:
        resp = requests.post(f"{JELLYSEERR_URL}/api/v1/request/{request_id}/approve", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return {"status": "success", "message": f"Request #{request_id} approved successfully."}
    except Exception as e:
        return {"error": f"Failed to approve request #{request_id}: {str(e)}"}

def jellyseerr_decline_request(request_id: int) -> dict:
    """Decline a pending media request in Jellyseerr."""
    if not _check_configured():
        return {"error": "Jellyseerr is not configured."}
    try:
        resp = requests.post(f"{JELLYSEERR_URL}/api/v1/request/{request_id}/decline", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return {"status": "success", "message": f"Request #{request_id} declined."}
    except Exception as e:
        return {"error": f"Failed to decline request #{request_id}: {str(e)}"}
