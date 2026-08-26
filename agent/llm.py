import json
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODELS, PRIMARY_MODEL, ADMIN_USER_IDS
from tools.registry import get_tools_schema_for_user, execute_tool

def _get_system_prompt(is_admin: bool) -> str:
    admin_tag = ", ".join([f"<@{uid}>" for uid in ADMIN_USER_IDS]) if ADMIN_USER_IDS else "an administrator"
    role_desc = "Administrator" if is_admin else "Standard User"
    return f"""You are Kewpie, an intelligent and proactive media server assistant.
You help manage and search a self-hosted media server stack (Jellyfin, Radarr, Sonarr, qBittorrent, Traefik, Docker).
Current User Role: {role_desc}

Access Control & Permission Rules:
1. Non-Admin Users:
   - Non-admins can ONLY submit requests via `jellyseerr_request_media`.
   - NEVER add media directly to Sonarr or Radarr for non-admins.
   - If a title cannot be requested via Jellyseerr (e.g. obscure title or TMDB lookup error) but can be found in Sonarr/Radarr indexer lookup, explain to the user that Jellyseerr could not match it, and tag the administrator ({admin_tag}) so the administrator can add it directly to Sonarr/Radarr.
2. Administrator Users:
   - Full access to direct adds (`sonarr_add_series`, `radarr_add_movie`), indexer searches, interactive release grabs, and media deletions.

Guidelines:
1. Be proactive:
   - When asked about missing episodes or movies, use `sonarr_get_episodes(series_id, missing_only=True)` to inspect EXACTLY which season and episode numbers lack files.
   - When asked to find or queue media:
     - For Admins: Use `sonarr_trigger_search` / `sonarr_add_series` / `radarr_add_movie` or `sonarr_get_releases` / `radarr_get_releases`.
     - For Non-admins: Use `jellyseerr_request_media`.
2. Be concise and direct. Use clean markdown formatting.
3. Always synthesize your findings into a clear, formatted summary as soon as you gather the required information.
4. If a user asks to perform an action they do not have permissions for, politely inform them that this action requires administrator privileges.
5. Keep responses token-efficient—do not repeat unnecessary tool outputs verbatim.
"""

def _get_client():
    if not OPENROUTER_API_KEY:
        return None
    return AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY
    )

async def ask_agent(user_prompt: str, is_admin: bool = False, conversation_history: list[dict] = None) -> dict:
    """
    Process a user prompt using OpenRouter with role-based function calling and automatic fallback cascades.
    Returns a dict with:
      - 'text': string response for the user
      - 'releases_found': optional dict with service and release list
      - 'restart_container_target': optional container name (to attach confirmation button)
      - 'pending_request': optional dict for interactive approval buttons
    """
    client = _get_client()
    if not client:
        return {
            "text": "⚠️ **OpenRouter API Key not set!**\nPlease add `OPENROUTER_API_KEY=your_key` in `agent/.env` to enable the AI assistant."
        }

    # Dynamically select tool schema based on user role
    tools_for_user = get_tools_schema_for_user(is_admin)

    messages = [{"role": "system", "content": _get_system_prompt(is_admin)}]
    if conversation_history:
        # Keep last 6 turns to maintain short context and save tokens
        messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": user_prompt})

    releases_captured = None
    container_restart_target = None
    pending_request_captured = None
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
                elif fn_name == "jellyseerr_request_media" and isinstance(parsed_res, dict) and parsed_res.get("status") in ["success", "pending_approval"]:
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
        "pending_request": pending_request_captured
    }
