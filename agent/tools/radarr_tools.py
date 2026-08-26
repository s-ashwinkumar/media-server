import requests
from config import RADARR_URL, RADARR_API_KEY

HEADERS = {
    "X-Api-Key": RADARR_API_KEY,
    "Content-Type": "application/json"
}

def _check_configured() -> bool:
    return bool(RADARR_URL and RADARR_API_KEY)

def radarr_search_movie(query: str, limit: int = 5) -> list[dict]:
    """Search for a movie in Radarr library or lookup new movies."""
    if not _check_configured():
        return [{"error": "Radarr is not configured or API key is missing."}]
    
    limit = min(max(1, limit), 5)
    try:
        # Search library first
        resp = requests.get(f"{RADARR_URL}/api/v3/movie", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        movies = resp.json()
        
        matches = [
            m for m in movies 
            if query.lower() in m.get("title", "").lower()
        ][:limit]
        
        if matches:
            return [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "hasFile": m.get("hasFile", False),
                    "monitored": m.get("monitored", False),
                    "sizeOnDisk_gb": round(m.get("sizeOnDisk", 0) / (1024**3), 2),
                    "status": m.get("status")
                }
                for m in matches
            ]
        
        # If not in library, do lookup
        lookup_resp = requests.get(
            f"{RADARR_URL}/api/v3/movie/lookup", 
            params={"term": query}, 
            headers=HEADERS, 
            timeout=10
        )
        lookup_resp.raise_for_status()
        lookup_results = lookup_resp.json()[:limit]
        
        return [
            {
                "tmdbId": m.get("tmdbId"),
                "title": m.get("title"),
                "year": m.get("year"),
                "inLibrary": m.get("id", 0) > 0,
                "overview": (m.get("overview", "")[:120] + "...") if m.get("overview") else ""
            }
            for m in lookup_results
        ]
    except Exception as e:
        return [{"error": f"Radarr API error: {str(e)}"}]

def radarr_get_releases(movie_id: int, limit: int = 5) -> list[dict]:
    """Search indexers for available releases of a movie in Radarr."""
    if not _check_configured():
        return [{"error": "Radarr is not configured or API key is missing."}]
    
    limit = min(max(1, limit), 5)
    try:
        resp = requests.get(
            f"{RADARR_URL}/api/v3/release", 
            params={"movieId": movie_id}, 
            headers=HEADERS, 
            timeout=25
        )
        resp.raise_for_status()
        releases = resp.json()
        
        valid_releases = [r for r in releases if not r.get("rejected", False)]
        valid_releases.sort(key=lambda x: x.get("seeders", 0), reverse=True)
        
        top_releases = (valid_releases if valid_releases else releases)[:limit]
        
        return [
            {
                "title": r.get("title"),
                "guid": r.get("guid"),
                "indexerId": r.get("indexerId"),
                "indexer": r.get("indexer"),
                "size_gb": round(r.get("size", 0) / (1024**3), 2),
                "seeders": r.get("seeders", 0),
                "leechers": r.get("leechers", 0),
                "quality": r.get("quality", {}).get("quality", {}).get("name", "Unknown"),
                "protocol": r.get("protocol", "torrent")
            }
            for r in top_releases
        ]
    except Exception as e:
        return [{"error": f"Failed to fetch releases: {str(e)}"}]

def radarr_trigger_search(movie_ids: list[int]) -> dict:
    """Trigger Radarr's automatic indexer search for specific movie IDs."""
    if not _check_configured():
        return {"error": "Radarr is not configured or API key is missing."}
    try:
        resp = requests.post(
            f"{RADARR_URL}/api/v3/command",
            json={"name": "MoviesSearch", "movieIds": movie_ids},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": "Automatic search command sent to Radarr successfully."}
    except Exception as e:
        return {"error": f"Failed to trigger movie search: {str(e)}"}

def radarr_refresh_movie(movie_id: int) -> dict:
    """Rescan disk and refresh metadata for a movie in Radarr."""
    if not _check_configured():
        return {"error": "Radarr is not configured or API key is missing."}
    try:
        resp = requests.post(
            f"{RADARR_URL}/api/v3/command",
            json={"name": "RefreshMovie", "movieId": movie_id},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": f"Disk rescan and metadata refresh triggered for movie {movie_id}."}
    except Exception as e:
        return {"error": f"Failed to refresh movie: {str(e)}"}

def radarr_add_movie(
    tmdb_id: int = None,
    query: str = None,
    quality_profile_id: int = 1,
    root_folder_path: str = "/movies",
    search_now: bool = True
) -> dict:
    """Add a new movie to Radarr library and optionally search indexers (Admin only)."""
    if not _check_configured():
        return {"error": "Radarr is not configured or API key is missing."}
    try:
        term = f"tmdb:{tmdb_id}" if tmdb_id else query
        if not term:
            return {"error": "Must provide either tmdb_id or query."}
            
        lookup_resp = requests.get(f"{RADARR_URL}/api/v3/movie/lookup", params={"term": term}, headers=HEADERS, timeout=15)
        lookup_resp.raise_for_status()
        lookup_results = lookup_resp.json()
        if not lookup_results:
            return {"error": f"No movie found matching '{term}' in Radarr lookup."}
            
        movie_data = lookup_results[0]
        
        payload = {
            "title": movie_data.get("title"),
            "titleSlug": movie_data.get("titleSlug"),
            "tmdbId": movie_data.get("tmdbId"),
            "year": movie_data.get("year"),
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "images": movie_data.get("images", []),
            "addOptions": {
                "searchForMovie": search_now
            }
        }
        
        add_resp = requests.post(f"{RADARR_URL}/api/v3/movie", json=payload, headers=HEADERS, timeout=20)
        add_resp.raise_for_status()
        added = add_resp.json()
        
        return {
            "status": "success",
            "movieId": added.get("id"),
            "title": added.get("title"),
            "message": f"Successfully added **{added.get('title')}** ({added.get('year')}) to Radarr and initiated indexer search."
        }
    except Exception as e:
        return {"error": f"Failed to add movie to Radarr: {str(e)}"}

def radarr_delete_movie(movie_id: int, delete_files: bool = True) -> dict:
    """Delete a movie and its media files from Radarr and disk."""
    if not _check_configured():
        return {"error": "Radarr is not configured or API key is missing."}
    try:
        resp = requests.delete(
            f"{RADARR_URL}/api/v3/movie/{movie_id}",
            params={"deleteFiles": "true" if delete_files else "false", "addImportExclusion": "false"},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": f"Movie #{movie_id} and its media files were successfully deleted from Radarr."}
    except Exception as e:
        return {"error": f"Failed to delete movie: {str(e)}"}

def radarr_grab_release(guid: str, indexer_id: int) -> dict:
    """Grab a specific release and send it to the download client."""
    if not _check_configured():
        return {"error": "Radarr is not configured or API key is missing."}
    try:
        resp = requests.post(
            f"{RADARR_URL}/api/v3/release",
            json={"guid": guid, "indexerId": indexer_id},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": "Release sent to download client successfully."}
    except Exception as e:
        return {"error": f"Failed to grab release: {str(e)}"}

def radarr_get_queue(limit: int = 5) -> list[dict]:
    """Get active Radarr downloads in progress."""
    if not _check_configured():
        return [{"error": "Radarr is not configured or API key is missing."}]
    limit = min(max(1, limit), 10)
    try:
        resp = requests.get(f"{RADARR_URL}/api/v3/queue", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        records = resp.json().get("records", [])[:limit]
        return [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "status": r.get("status"),
                "trackedDownloadStatus": r.get("trackedDownloadStatus"),
                "trackedDownloadState": r.get("trackedDownloadState"),
                "sizeleft_gb": round(r.get("sizeleft", 0) / (1024**3), 2),
                "timeleft": r.get("timeleft", "Unknown"),
                "errorMessage": r.get("errorMessage", "")
            }
            for r in records
        ]
    except Exception as e:
        return [{"error": f"Failed to fetch Radarr queue: {str(e)}"}]
