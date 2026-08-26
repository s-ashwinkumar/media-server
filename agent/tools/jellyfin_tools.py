import requests
from config import JELLYFIN_URL, JELLYFIN_API_KEY

HEADERS = {
    "X-Emby-Token": JELLYFIN_API_KEY,
    "Content-Type": "application/json"
}

def _check_configured() -> bool:
    return bool(JELLYFIN_URL and JELLYFIN_API_KEY)

def jellyfin_get_active_streams() -> list[dict]:
    """Get real-time active streaming sessions and transcode details on Jellyfin."""
    if not _check_configured():
        return [{"error": "Jellyfin is not configured or API key is missing."}]
    try:
        resp = requests.get(f"{JELLYFIN_URL}/Sessions", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        sessions = resp.json()
        
        active = []
        for s in sessions:
            now_playing = s.get("NowPlayingItem")
            if not now_playing:
                continue
            
            play_state = s.get("PlayState", {})
            transcoding_info = s.get("TranscodingInfo", {})
            is_transcoding = bool(transcoding_info)
            
            active.append({
                "user": s.get("UserName", "Unknown"),
                "client": s.get("Client", "Unknown"),
                "device": s.get("DeviceName", "Unknown"),
                "title": now_playing.get("Name", "Unknown"),
                "seriesName": now_playing.get("SeriesName", ""),
                "mediaType": now_playing.get("Type", "Unknown"),
                "playbackMethod": "Transcoding" if is_transcoding else "DirectPlay",
                "videoCodec": transcoding_info.get("VideoCodec") or now_playing.get("Container", "Direct"),
                "isPaused": play_state.get("IsPaused", False)
            })
            
        return active if active else [{"message": "No active streaming sessions right now."}]
    except Exception as e:
        return [{"error": f"Failed to get Jellyfin active streams: {str(e)}"}]

def jellyfin_scan_library() -> dict:
    """Trigger a full Jellyfin library refresh / scan."""
    if not _check_configured():
        return {"error": "Jellyfin is not configured."}
    try:
        resp = requests.post(f"{JELLYFIN_URL}/Library/Refresh", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return {"status": "success", "message": "Jellyfin library scan triggered successfully."}
    except Exception as e:
        return {"error": f"Failed to trigger Jellyfin scan: {str(e)}"}
