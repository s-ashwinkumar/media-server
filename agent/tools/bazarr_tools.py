import requests
from config import BAZARR_URL, BAZARR_API_KEY

HEADERS = {
    "X-API-KEY": BAZARR_API_KEY,
    "Content-Type": "application/json"
}

def _check_configured() -> bool:
    return bool(BAZARR_URL and BAZARR_API_KEY)

def bazarr_get_missing_subtitles(limit: int = 5) -> dict:
    """Get list of movies and TV episodes currently missing subtitles in Bazarr."""
    if not _check_configured():
        return {"error": "Bazarr is not configured or API key is missing."}
    limit = min(max(1, limit), 10)
    try:
        ep_resp = requests.get(f"{BAZARR_URL}/api/episodes/wanted", params={"length": limit}, headers=HEADERS, timeout=10)
        ep_data = ep_resp.json().get("data", []) if ep_resp.ok else []
        
        movie_resp = requests.get(f"{BAZARR_URL}/api/movies/wanted", params={"length": limit}, headers=HEADERS, timeout=10)
        movie_data = movie_resp.json().get("data", []) if movie_resp.ok else []
        
        missing_episodes = [
            {"series": e.get("seriesTitle"), "episode": f"S{e.get('seasonNumber')}E{e.get('episodeNumber')}", "title": e.get("episodeTitle"), "missing": e.get("missing_subtitles")}
            for e in ep_data[:limit]
        ]
        missing_movies = [
            {"title": m.get("title"), "year": m.get("year"), "missing": m.get("missing_subtitles")}
            for m in movie_data[:limit]
        ]
        
        return {
            "missing_episodes": missing_episodes if missing_episodes else "None",
            "missing_movies": missing_movies if missing_movies else "None"
        }
    except Exception as e:
        return {"error": f"Failed to get missing subtitles from Bazarr: {str(e)}"}
