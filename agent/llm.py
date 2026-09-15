import json
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODELS, PRIMARY_MODEL, ADMIN_USER_IDS
from tools.registry import get_tools_schema_for_user, execute_tool

def _get_system_prompt(is_admin: bool) -> str:
    if not is_admin:
        return """You are Kewpie, a friendly, concise, and helpful media assistant for this server.
Your role is to help server members check if movies or TV shows are available to watch, search the catalog, and submit media requests.

Available Capabilities:
1. Search Catalog: Use `jellyseerr_search` to check if a title exists, and see whether it is already Available to watch on the server, Downloading/Processing, or Available to Request.
2. Request Media: Use `jellyseerr_request_media` to submit a request for a movie or TV show (you can specify specific season numbers for TV series).
3. Check Requests: Use `jellyseerr_list_requests` to check the status of recent requests.
4. Active Streams: Use `jellyfin_get_active_streams` if asked what is currently playing.

Privacy & Security Rules (STRICT):
- NEVER mention internal backend tools, download clients, or infrastructure names (such as Radarr, Sonarr, qBittorrent, Prowlarr, Docker, Traefik, Bazarr, APIs, tokens, or containers).
- NEVER discuss admin permissions, restrictions, or backend plumbing with users.
- If a title cannot be found in the catalog or requested:
  - If `jellyseerr_request_media` indicates the request was forwarded to the administrator, inform the user warmly: "I couldn't find an exact match in the public catalog, but I've forwarded your request to the server admin for review!"
  - If completely unfound, politely state that you could not locate that title in the catalog, but that an admin can look into adding it manually.
  - NEVER say "you don't have permission to add via Radarr/Sonarr".
- FACTUAL INTEGRITY: NEVER claim an action was completed, submitted, or linked unless the tool was executed in this exact turn and returned a successful response. Never invent or assume success.
- Be conversational, warm, and concise. Use clean markdown formatting (bold titles, release years).
"""

    return f"""You are Kewpie, an intelligent, proactive, and strictly honest media server assistant for the system administrator.
You help manage and automate the self-hosted media server stack (Jellyseerr, Jellyfin, Radarr, Sonarr, Prowlarr, qBittorrent, SABnzbd, Docker, System Storage).

CRITICAL WORKFLOW RULES FOR MEDIA REQUESTS (MANDATORY FOR ALL USERS & ADMINS):
1. ALWAYS USE JELLYSEERR FIRST:
   - When asked to download, queue, add, or request any movie or TV show (e.g. "queue up Slow Horses season 1", "add movie Inception", "download Severance"), you MUST ALWAYS call `jellyseerr_request_media` first.
   - For TV shows with specific seasons requested, pass them to `jellyseerr_request_media(title=..., media_type="tv", seasons=[1])`.
   - DO NOT bypass Jellyseerr to call `sonarr_add_series` or `radarr_add_movie` directly. Jellyseerr is the single source of truth for the media queue, user logs, notifications, and library syncing.
2. DIRECT SONARR / RADARR ADDS ARE EMERGENCY-ONLY:
   - ONLY use `sonarr_add_series` or `radarr_add_movie` if:
     a) `jellyseerr_request_media` or `jellyseerr_search` cannot find the title (e.g. obscure title not in TMDB/TVDB), OR
     b) The administrator explicitly commands you to bypass Jellyseerr (e.g. "Force add directly to Sonarr", "Bypass Jellyseerr").
3. STRICT FACTUAL INTEGRITY (ZERO HALLUCINATION):
   - NEVER claim an action was taken, submitted, or linked unless you actually called the corresponding tool in this turn and received a successful response.
   - If an API or tool returns an error or indicates media is already present (e.g. "already present in your server library"), report that exact factual status immediately. NEVER pretend, guess, or invent that "Jellyseerr linked the request to Sonarr" when it did not.
   - When the admin asks "Why isn't X showing up in Jellyseerr?", check with `jellyseerr_list_requests` or `jellyseerr_search` before answering.
4. Maintenance & Diagnostics:
   - When asked about missing episodes for a series already in Sonarr, use `sonarr_get_episodes(series_id, missing_only=True)`.
   - When asked to inspect releases or grab torrents manually, use `sonarr_get_releases` / `radarr_get_releases`.
   - Use `list_docker_containers`, `restart_docker_container`, `get_disk_space`, `get_system_stats` for system diagnostics.
5. Be concise, direct, and technically precise. Use clean markdown formatting.
"""

def _get_client():
    if not OPENROUTER_API_KEY:
        return None
    return AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY
    )

async def ask_agent(
    user_prompt: str, 
    is_admin: bool = False, 
    conversation_history: list[dict] = None,
    ambient_context: str = ""
) -> dict:
    """
    Process a user prompt using OpenRouter with role-based function calling and automatic fallback cascades.
    Returns a dict with:
      - 'text': string response for the user
      - 'releases_found': optional dict with service and release list
      - 'restart_container_target': optional container name (to attach confirmation button)
      - 'pending_request': optional dict for interactive approval buttons
      - 'admin_fallback': optional dict when unmatched media is found in Radarr/Sonarr for admin DM
    """
    client = _get_client()
    if not client:
        return {
            "text": "⚠️ **OpenRouter API Key not set!**\nPlease add `OPENROUTER_API_KEY=your_key` in `agent/.env` to enable the AI assistant."
        }

    # Dynamically select tool schema based on user role
    tools_for_user = get_tools_schema_for_user(is_admin)

    messages = [{"role": "system", "content": _get_system_prompt(is_admin)}]
    if ambient_context:
        messages.append({
            "role": "system",
            "content": f"[Recent channel conversation for context]:\n{ambient_context}"
        })
    if conversation_history:
        # Keep last 6 turns to maintain short context and save tokens
        messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": user_prompt})

    releases_captured = None
    container_restart_target = None
    pending_request_captured = None
    admin_fallback_captured = None
    max_steps = 8
    step_count = 0
    last_message = None

    while step_count < max_steps:
        step_count += 1
        response = None
        
        # 1. Attempt primary OpenRouter call with the top 3 models in the fallback array
        try:
            extra_body = {
                "models": OPENROUTER_MODELS[:3],  # OpenRouter requires max 3 in the array
                "route": "fallback",
                "provider": {
                    "order": ["Google AI Studio"],
                    "allow_fallbacks": False
                }
            }
            kwargs = {
                "model": PRIMARY_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "extra_body": extra_body
            }
            if tools_for_user:
                kwargs["tools"] = tools_for_user
                kwargs["tool_choice"] = "auto"

            response = await client.chat.completions.create(**kwargs)
        except Exception as primary_err:
            # 2. If the first 3 models fail, attempt the 4th model or return clean error
            fallback_model = OPENROUTER_MODELS[3] if len(OPENROUTER_MODELS) > 3 else OPENROUTER_MODELS[-1]
            try:
                kwargs_fb = {
                    "model": fallback_model,
                    "messages": messages,
                    "temperature": 0.2,
                    "extra_body": {
                        "provider": {
                            "order": ["Google AI Studio"],
                            "allow_fallbacks": False
                        }
                    }
                }
                if tools_for_user:
                    kwargs_fb["tools"] = tools_for_user
                    kwargs_fb["tool_choice"] = "auto"
                response = await client.chat.completions.create(**kwargs_fb)
            except Exception as fb_err:
                return {"text": f"❌ Error communicating with OpenRouter BYOK: {str(primary_err)} | Fallback: {str(fb_err)}"}

        message = response.choices[0].message
        last_message = message
        messages.append(message.model_dump(exclude_none=True))

        # If LLM didn't call any tools, we have our final text answer
        if not message.tool_calls:
            return {
                "text": message.content or "Done.",
                "releases_found": releases_captured,
                "restart_container_target": container_restart_target,
                "pending_request": pending_request_captured
            }

        # Handle tool calls
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except Exception:
                fn_args = {}

            # Execute tool with role check
            tool_result_str = execute_tool(fn_name, fn_args, is_admin=is_admin)

            # Check if this tool returned releases, restarts, or requests for Discord UI
            try:
                parsed_res = json.loads(tool_result_str)
                if is_admin and fn_name in ["radarr_get_releases", "sonarr_get_releases"] and isinstance(parsed_res, list) and len(parsed_res) > 0 and "guid" in parsed_res[0]:
                    releases_captured = {
                        "service": "sonarr" if fn_name == "sonarr_get_releases" else "radarr",
                        "items": parsed_res
                    }
                elif is_admin and fn_name == "restart_docker_container":
                    container_restart_target = fn_args.get("container_name")
                elif fn_name == "jellyseerr_request_media" and isinstance(parsed_res, dict):
                    if parsed_res.get("status") in ["unmatched_found_in_radarr", "unmatched_found_in_sonarr"]:
                        admin_fallback_captured = {
                            "title": parsed_res.get("title"),
                            "year": parsed_res.get("year"),
                            "mediaType": parsed_res.get("mediaType", "movie"),
                            "id": parsed_res.get("tmdbId") if parsed_res.get("status") == "unmatched_found_in_radarr" else parsed_res.get("tvdbId")
                        }
                    elif parsed_res.get("status") in ["success", "pending_approval"]:
                        pending_request_captured = {
                            "request_id": parsed_res.get("requestId"),
                            "title": parsed_res.get("title"),
                            "mediaType": parsed_res.get("mediaType", "movie"),
                            "mediaId": parsed_res.get("mediaId")
                        }
            except Exception:
                pass

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_str
            })

    # If reached max steps without a final text message, force a final synthesis turn without tools
    final_text = None
    if last_message and last_message.content:
        final_text = last_message.content
    else:
        try:
            final_res = await client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=messages,
                temperature=0.2
            )
            final_text = final_res.choices[0].message.content
        except Exception:
            final_text = "Here are the results of your media request."

    return {
        "text": final_text or "Done.",
        "releases_found": releases_captured,
        "restart_container_target": container_restart_target,
        "pending_request": pending_request_captured,
        "admin_fallback": admin_fallback_captured
    }
