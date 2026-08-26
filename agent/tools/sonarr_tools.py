import requests
from config import SONARR_URL, SONARR_API_KEY

HEADERS = {
    "X-Api-Key": SONARR_API_KEY,
    "Content-Type": "application/json"
}

def _check_configured() -> bool:
    return bool(SONARR_URL and SONARR_API_KEY)

def sonarr_search_series(query: str, limit: int = 5) -> list[dict]:
    """Search for TV series in Sonarr library or lookup new series."""
    if not _check_configured():
        return [{"error": "Sonarr is not configured or API key is missing."}]
    
    limit = min(max(1, limit), 5)
    try:
        # Search library first
        resp = requests.get(f"{SONARR_URL}/api/v3/series", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        series_list = resp.json()
        
        matches = [
            s for s in series_list 
            if query.lower() in s.get("title", "").lower()
        ][:limit]
        
        if matches:
            return [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "seasonCount": m.get("seasonCount", 0),
                    "episodeCount": m.get("statistics", {}).get("episodeCount", 0),
                    "episodeFileCount": m.get("statistics", {}).get("episodeFileCount", 0),
                    "percentOfEpisodes": m.get("statistics", {}).get("percentOfEpisodes", 0),
                    "status": m.get("status"),
                    "monitored": m.get("monitored", False)
                }
                for m in matches
            ]
        
        # If not found in library, lookup
        lookup_resp = requests.get(
            f"{SONARR_URL}/api/v3/series/lookup", 
            params={"term": query}, 
            headers=HEADERS, 
            timeout=10
        )
        lookup_resp.raise_for_status()
        lookup_results = lookup_resp.json()[:limit]
        
        return [
            {
                "tvdbId": l.get("tvdbId"),
                "title": l.get("title"),
                "year": l.get("year"),
                "inLibrary": l.get("id", 0) > 0,
                "overview": (l.get("overview", "")[:120] + "...") if l.get("overview") else ""
            }
            for l in lookup_results
        ]
    except Exception as e:
        return [{"error": f"Sonarr API error: {str(e)}"}]

def sonarr_get_episodes(series_id: int, missing_only: bool = True) -> list[dict]:
    """Get episodes for a series in Sonarr, filtering by missing/downloaded status."""
    if not _check_configured():
        return [{"error": "Sonarr is not configured or API key is missing."}]
    try:
        resp = requests.get(
            f"{SONARR_URL}/api/v3/episode",
            params={"seriesId": series_id},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        episodes = resp.json()
        
        results = []
        for ep in episodes:
            has_file = ep.get("hasFile", False)
            monitored = ep.get("monitored", False)
            
            # If missing_only, only include episodes that are monitored but have no file
            if missing_only and (has_file or not monitored):
                continue
                
            results.append({
                "episodeId": ep.get("id"),
                "seasonNumber": ep.get("seasonNumber"),
                "episodeNumber": ep.get("episodeNumber"),
                "title": ep.get("title"),
                "hasFile": has_file,
                "monitored": monitored,
                "airDate": ep.get("airDate", "N/A")
            })
            
        return results[:15]
    except Exception as e:
        return [{"error": f"Failed to get episodes: {str(e)}"}]

def sonarr_trigger_search(episode_ids: list[int] = None, series_id: int = None) -> dict:
    """Trigger Sonarr's automatic indexer search for specific episode IDs or an entire series."""
    if not _check_configured():
        return {"error": "Sonarr is not configured or API key is missing."}
    try:
        payload = {}
        if episode_ids:
            payload = {"name": "EpisodeSearch", "episodeIds": episode_ids}
        elif series_id:
            payload = {"name": "SeriesSearch", "seriesId": series_id}
        else:
            return {"error": "Must provide either episode_ids or series_id."}

        resp = requests.post(f"{SONARR_URL}/api/v3/command", json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return {"status": "success", "message": "Automatic search command sent to Sonarr successfully."}
    except Exception as e:
        return {"error": f"Failed to trigger search: {str(e)}"}

def sonarr_refresh_series(series_id: int) -> dict:
    """Rescan disk and refresh metadata for a series in Sonarr."""
    if not _check_configured():
        return {"error": "Sonarr is not configured or API key is missing."}
    try:
        resp = requests.post(
            f"{SONARR_URL}/api/v3/command",
            json={"name": "RefreshSeries", "seriesId": series_id},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": f"Disk rescan and metadata refresh triggered for series {series_id}."}
    except Exception as e:
        return {"error": f"Failed to refresh series: {str(e)}"}

def sonarr_add_series(
    tvdb_id: int = None,
    query: str = None,
    seasons_to_monitor: list[int] = None,
    quality_profile_id: int = 1,
    root_folder_path: str = "/tv",
    search_missing: bool = True
) -> dict:
    """Add a new TV series to Sonarr library and optionally search for missing episodes (Admin only)."""
    if not _check_configured():
        return {"error": "Sonarr is not configured or API key is missing."}
    try:
        term = f"tvdb:{tvdb_id}" if tvdb_id else query
        if not term:
            return {"error": "Must provide either tvdb_id or query."}
            
        lookup_resp = requests.get(f"{SONARR_URL}/api/v3/series/lookup", params={"term": term}, headers=HEADERS, timeout=15)
        lookup_resp.raise_for_status()
        lookup_results = lookup_resp.json()
        if not lookup_results:
            return {"error": f"No series found matching '{term}' in Sonarr lookup."}
            
        series_data = lookup_results[0]
        
        # Configure seasons monitoring
        seasons = series_data.get("seasons", [])
        if seasons_to_monitor:
            monitored_seasons = [
                {"seasonNumber": s.get("seasonNumber"), "monitored": (s.get("seasonNumber") in seasons_to_monitor)}
                for s in seasons
            ]
        else:
            monitored_seasons = [
                {"seasonNumber": s.get("seasonNumber"), "monitored": True}
                for s in seasons
            ]
            
        payload = {
            "title": series_data.get("title"),
            "titleSlug": series_data.get("titleSlug"),
            "tvdbId": series_data.get("tvdbId"),
            "year": series_data.get("year"),
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "seasonFolder": True,
            "images": series_data.get("images", []),
            "seasons": monitored_seasons,
            "addOptions": {
                "searchForMissingEpisodes": search_missing
            }
        }
        
        add_resp = requests.post(f"{SONARR_URL}/api/v3/series", json=payload, headers=HEADERS, timeout=20)
        add_resp.raise_for_status()
        added = add_resp.json()
        
        season_desc = f"Season(s) {seasons_to_monitor}" if seasons_to_monitor else "all seasons"
        return {
            "status": "success",
            "seriesId": added.get("id"),
            "title": added.get("title"),
            "message": f"Successfully added **{added.get('title')}** ({added.get('year')}) to Sonarr, monitoring {season_desc} and initiating episode searches."
        }
    except Exception as e:
        return {"error": f"Failed to add series to Sonarr: {str(e)}"}

def sonarr_delete_series(series_id: int, delete_files: bool = True) -> dict:
    """Delete a TV series and its media files from Sonarr and disk."""
    if not _check_configured():
        return {"error": "Sonarr is not configured or API key is missing."}
    try:
        resp = requests.delete(
            f"{SONARR_URL}/api/v3/series/{series_id}",
            params={"deleteFiles": "true" if delete_files else "false", "addImportListExclusion": "false"},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": f"Series #{series_id} and its media files were successfully deleted from Sonarr."}
    except Exception as e:
        return {"error": f"Failed to delete series: {str(e)}"}

def sonarr_get_releases(episode_id: int, limit: int = 5) -> list[dict]:
    """Search indexers for available releases of a specific episode in Sonarr."""
    if not _check_configured():
        return [{"error": "Sonarr is not configured or API key is missing."}]
    limit = min(max(1, limit), 5)
    try:
        resp = requests.get(
            f"{SONARR_URL}/api/v3/release",
            params={"episodeId": episode_id},
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
                "quality": r.get("quality", {}).get("quality", {}).get("name", "Unknown")
            }
            for r in top_releases
        ]
    except Exception as e:
        return [{"error": f"Failed to fetch Sonarr releases: {str(e)}"}]

def sonarr_grab_release(guid: str, indexer_id: int) -> dict:
    """Grab a specific release for Sonarr."""
    if not _check_configured():
        return {"error": "Sonarr is not configured or API key is missing."}
    try:
        resp = requests.post(
            f"{SONARR_URL}/api/v3/release",
            json={"guid": guid, "indexerId": indexer_id},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        return {"status": "success", "message": "Episode release sent to download client successfully."}
    except Exception as e:
        return {"error": f"Failed to grab Sonarr release: {str(e)}"}

def sonarr_get_queue(limit: int = 5) -> list[dict]:
    """Get active Sonarr episode downloads in progress."""
    if not _check_configured():
        return [{"error": "Sonarr is not configured or API key is missing."}]
    limit = min(max(1, limit), 10)
    try:
        resp = requests.get(f"{SONARR_URL}/api/v3/queue", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        records = resp.json().get("records", [])[:limit]
        return [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "status": r.get("status"),
                "trackedDownloadStatus": r.get("trackedDownloadStatus"),
                "sizeleft_gb": round(r.get("sizeleft", 0) / (1024**3), 2),
                "timeleft": r.get("timeleft", "Unknown"),
                "errorMessage": r.get("errorMessage", "")
            }
            for r in records
        ]
    except Exception as e:
        return [{"error": f"Failed to fetch Sonarr queue: {str(e)}"}]
