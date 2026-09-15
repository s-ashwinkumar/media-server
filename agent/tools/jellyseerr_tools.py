import re
import requests
from config import (
    JELLYSEERR_URL,
    JELLYSEERR_API_KEY,
    JELLYSEERR_BOT_EMAIL,
    JELLYSEERR_BOT_PASSWORD,
    RADARR_URL,
    RADARR_API_KEY,
    SONARR_URL,
    SONARR_API_KEY
)

HEADERS = {
    "X-Api-Key": JELLYSEERR_API_KEY,
    "Content-Type": "application/json"
}

_bot_session = None

def _extract_seasons(query: str, seasons: any = None) -> tuple[str, any]:
    """
    Extracts season numbers from arguments or title string.
    e.g. ('Slow Horses Season 1', 'all') -> ('Slow Horses', [1])
         ('Slow Horses S01-S02', 'all') -> ('Slow Horses', [1, 2])
         ('Slow Horses', [1]) -> ('Slow Horses', [1])
    """
    parsed_seasons = None
    if seasons and seasons != "all":
        if isinstance(seasons, int):
            parsed_seasons = [seasons]
        elif isinstance(seasons, list):
            parsed_seasons = [int(s) for s in seasons if str(s).isdigit()]
        elif isinstance(seasons, str):
            digits = re.findall(r'\b\d+\b', seasons)
            if digits:
                parsed_seasons = [int(d) for d in digits]

    clean_query = query
    if not parsed_seasons:
        word_to_num = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
        }
        normalized_q = query
        for word, num in word_to_num.items():
            normalized_q = re.sub(rf'\b(?:season|s)\s+{word}\b', f'season {num}', normalized_q, flags=re.IGNORECASE)

        pattern = r"\b(?:season|s)\s*(\d+)(?:\s*(?:-|to)\s*(?:season|s)?\s*(\d+))?\b"
        s_match = re.search(pattern, normalized_q, re.IGNORECASE)
        if s_match:
            start_s = int(s_match.group(1))
            end_s = int(s_match.group(2)) if s_match.group(2) else start_s
            parsed_seasons = list(range(start_s, end_s + 1))
            clean_query = re.sub(pattern, "", normalized_q, flags=re.IGNORECASE)
            for word in word_to_num.keys():
                clean_query = re.sub(rf"\b(?:season|s)\s+{word}\b", "", clean_query, flags=re.IGNORECASE)
            clean_query = re.sub(r"\s+", " ", clean_query).strip(" -:;,.")

    return clean_query or query, parsed_seasons or "all"

def _sanitize_query(query: str) -> tuple[str, str | None]:
    """
    Extracts 4-digit release year if present and returns (clean_query, year_str).
    e.g. 'Dune: Part Two (2024)' -> ('Dune: Part Two', '2024')
         'The Matrix 1999' -> ('The Matrix', '1999')
    """
    cleaned = query.strip()
    year_match = re.search(r'[\(\[\{]?\b((?:19|20)\d{2})\b[\)\]\}]?', cleaned)
    year = None
    if year_match:
        year = year_match.group(1)
        cleaned = re.sub(r'[\(\[\{]?\b(?:19|20)\d{2}\b[\)\]\}]?', '', cleaned).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(" -:;,.")
    return cleaned or query.strip(), year

def _search_jellyseerr_raw(title: str, year: str = None) -> tuple[list[dict], str | None]:
    """Execute search in Jellyseerr with query sanitization and fallback."""
    title_no_seasons, _ = _extract_seasons(title)
    clean_title, extracted_year = _sanitize_query(title_no_seasons)
    target_year = year or extracted_year

    results = []
    try:
        resp = requests.get(
            f"{JELLYSEERR_URL}/api/v1/search", 
            params={"query": clean_title}, 
            headers=HEADERS, 
            timeout=10
        )
        if resp.ok:
            results = resp.json().get("results", [])
    except Exception:
        pass

    # If no results and title had extra words/symbols, try raw title
    if not results and clean_title != title:
        try:
            resp = requests.get(
                f"{JELLYSEERR_URL}/api/v1/search", 
                params={"query": title}, 
                headers=HEADERS, 
                timeout=10
            )
            if resp.ok:
                results = resp.json().get("results", [])
        except Exception:
            pass

    return results, target_year

def _check_radarr_fallback(title: str, year: str = None) -> dict | None:
    """Silently check Radarr's metadata lookup if Jellyseerr TMDB search yields no results."""
    if not RADARR_URL or not RADARR_API_KEY:
        return None
    try:
        clean_title, extracted_year = _sanitize_query(title)
        target_year = year or extracted_year
        resp = requests.get(
            f"{RADARR_URL}/api/v3/movie/lookup",
            params={"term": clean_title},
            headers={"X-Api-Key": RADARR_API_KEY},
            timeout=8
        )
        if resp.ok:
            results = resp.json()
            if results and isinstance(results, list):
                if target_year:
                    for m in results:
                        if str(m.get("year")) == str(target_year):
                            return m
                return results[0]
    except Exception:
        pass
    return None

def _check_sonarr_fallback(title: str, year: str = None) -> dict | None:
    """Silently check Sonarr's metadata lookup if Jellyseerr TVDB search yields no results."""
    if not SONARR_URL or not SONARR_API_KEY:
        return None
    try:
        clean_title, extracted_year = _sanitize_query(title)
        target_year = year or extracted_year
        resp = requests.get(
            f"{SONARR_URL}/api/v3/series/lookup",
            params={"term": clean_title},
            headers={"X-Api-Key": SONARR_API_KEY},
            timeout=8
        )
        if resp.ok:
            results = resp.json()
            if results and isinstance(results, list):
                if target_year:
                    for s in results:
                        if str(s.get("year")) == str(target_year):
                            return s
                return results[0]
    except Exception:
        pass
    return None

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

STATUS_NAMES = {
    1: "Available to Request",
    2: "Pending Approval",
    3: "Processing / Downloading",
    4: "Partially Available",
    5: "Available to Watch (In Library)"
}

def jellyseerr_search(query: str, media_type: str = "all", limit: int = 5) -> list[dict]:
    """
    Search for movies and TV shows in the media catalog, checking current availability.
    Returns title, release year, media type, and server availability status.
    """
    if not _check_configured():
        return [{"error": "Jellyseerr is not configured or API key is missing."}]
    
    results, target_year = _search_jellyseerr_raw(query)
    if not results:
        # Check fallback in Radarr/Sonarr to report existence if available
        radarr_match = _check_radarr_fallback(query)
        if radarr_match:
            return [{
                "title": radarr_match.get("title"),
                "year": str(radarr_match.get("year", "")),
                "mediaType": "movie",
                "availability": "Available via Admin Request",
                "overview": (radarr_match.get("overview") or "")[:140]
            }]
        return [{"message": f"No titles found matching '{query}' in the catalog."}]

    limit = min(max(1, limit), 10)
    
    # Filter by media_type if specified
    filtered = []
    for r in results:
        rtype = r.get("mediaType")
        if media_type.lower() in ["movie", "film"] and rtype != "movie":
            continue
        if media_type.lower() in ["tv", "series", "show"] and rtype != "tv":
            continue
        filtered.append(r)

    if not filtered:
        filtered = results

    # If a year was specified, sort matching year first
    if target_year:
        def year_sort_key(item):
            item_yr = (item.get("releaseDate") or item.get("firstAirDate") or "")[:4]
            return 0 if item_yr == str(target_year) else 1
        filtered.sort(key=year_sort_key)

    output = []
    for r in filtered[:limit]:
        media_info = r.get("mediaInfo") or {}
        status_code = media_info.get("status", 1)
        status_str = STATUS_NAMES.get(status_code, "Available to Request")
        year_str = (r.get("releaseDate") or r.get("firstAirDate") or "")[:4]
        title_str = r.get("title") or r.get("name") or "Unknown"

        output.append({
            "id": r.get("id"),
            "title": title_str,
            "mediaType": r.get("mediaType", "movie"),
            "year": year_str,
            "availability": status_str,
            "isAvailable": status_code == 5,
            "overview": (r.get("overview") or "")[:140]
        })

    return output

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

def jellyseerr_request_media(title: str, media_type: str = "movie", seasons: any = "all", is_admin: bool = False, force_approve: bool = False) -> dict:
    """
    Search and submit media requests directly to Jellyseerr.
    - If requested by non-admin: Submits via kewpie-bot user session so it enters Jellyseerr as 'Pending Approval' (status: 1).
    - If requested by admin: Submits via Admin API key (auto-approved and queued for download).
    - If title is not found in Jellyseerr catalog: Silently checks Radarr/Sonarr indexers and flags for admin approval.
    - If media is a TV series and specific seasons are requested, only those seasons are queued.
    """
    if not _check_configured():
        return {"error": "Jellyseerr is not configured."}
    try:
        clean_title_no_season, parsed_seasons = _extract_seasons(title, seasons)
        results, target_year = _search_jellyseerr_raw(clean_title_no_season)
        
        # If Jellyseerr fails to find it, trigger the silent Radarr/Sonarr fallback
        if not results:
            if media_type.lower() in ["tv", "series", "show"]:
                sonarr_match = _check_sonarr_fallback(clean_title_no_season, target_year)
                if sonarr_match:
                    return {
                        "status": "unmatched_found_in_sonarr",
                        "title": sonarr_match.get("title"),
                        "year": str(sonarr_match.get("year", "")),
                        "tvdbId": sonarr_match.get("tvdbId"),
                        "mediaType": "tv",
                        "overview": (sonarr_match.get("overview") or "")[:140],
                        "message": f"Couldn't find an exact match in the public catalog for '{title}', but located **{sonarr_match.get('title')}** in indexers. Forwarded to the server administrator for review."
                    }
            else:
                radarr_match = _check_radarr_fallback(clean_title_no_season, target_year)
                if radarr_match:
                    return {
                        "status": "unmatched_found_in_radarr",
                        "title": radarr_match.get("title"),
                        "year": str(radarr_match.get("year", "")),
                        "tmdbId": radarr_match.get("tmdbId"),
                        "mediaType": "movie",
                        "overview": (radarr_match.get("overview") or "")[:140],
                        "message": f"Couldn't find an exact match in the public catalog for '{title}', but located **{radarr_match.get('title')}** in indexers. Forwarded to the server administrator for review."
                    }
            return {"error": f"Could not find any movie or TV show matching '{title}' in the catalog or indexers."}
        
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
            payload["seasons"] = parsed_seasons

        season_desc = f" (Season {', '.join(map(str, parsed_seasons))})" if isinstance(parsed_seasons, list) else ""

        # Non-admin request
        if not is_admin and not force_approve:
            bot_session = _get_bot_session()
            session_to_use = bot_session if bot_session else requests
            h = {} if bot_session else HEADERS
            req_resp = session_to_use.post(f"{JELLYSEERR_URL}/api/v1/request", json=payload, headers=h, timeout=15)
        else:
            # Admin request (auto-approved via admin API key)
            req_resp = requests.post(f"{JELLYSEERR_URL}/api/v1/request", json=payload, headers=HEADERS, timeout=15)

        if req_resp.ok:
            req_data = req_resp.json()
            req_id = req_data.get("id")
            if not is_admin and not force_approve:
                return {
                    "status": "pending_approval",
                    "requestId": req_id,
                    "title": media_title,
                    "year": year,
                    "mediaType": actual_type,
                    "message": f"Submitted request for **{media_title}**{season_desc} (#{req_id}) into Jellyseerr. It is **Pending Approval** by an administrator."
                }
            return {
                "status": "success",
                "requestId": req_id,
                "title": media_title,
                "year": year,
                "mediaType": actual_type,
                "message": f"Successfully approved and queued **{media_title}**{season_desc} (#{req_id}) in Jellyseerr for download!"
            }

        # If request was not OK (e.g. 400 or 409 Conflict)
        try:
            err_json = req_resp.json()
            err_msg = err_json.get("message") or err_json.get("error") or req_resp.text
        except Exception:
            err_msg = req_resp.text

        err_lower = str(err_msg).lower()
        if "already exists" in err_lower or "already requested" in err_lower or "already available" in err_lower:
            return {
                "status": "already_exists",
                "title": media_title,
                "year": year,
                "mediaType": actual_type,
                "message": f"ℹ️ **{media_title}**{season_desc} is already present in your server library or has already been requested in Jellyseerr. Jellyseerr does not permit duplicate requests."
            }

        return {"error": f"Failed to submit Jellyseerr request (HTTP {req_resp.status_code}): {err_msg}"}
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
