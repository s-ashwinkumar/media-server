import docker

def _get_docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None

def list_docker_containers() -> list[dict]:
    """List all running and stopped Docker containers with their status and health."""
    client = _get_docker_client()
    if not client:
        return [{"error": "Cannot connect to Docker daemon. Ensure docker is running and permissions are granted."}]
    
    try:
        containers = client.containers.list(all=True)
        results = []
        for c in containers:
            health = c.attrs.get("State", {}).get("Health", {}).get("Status", "N/A")
            results.append({
                "name": c.name,
                "status": c.status,
                "health": health,
                "image": c.image.tags[0] if c.image.tags else "unknown"
            })
        return results
    except Exception as e:
        return [{"error": f"Docker error: {str(e)}"}]

def restart_docker_container(container_name: str) -> dict:
    """Restart a specific Docker container safely."""
    client = _get_docker_client()
    if not client:
        return {"error": "Cannot connect to Docker daemon."}
    
    try:
        container = client.containers.get(container_name)
        container.restart(timeout=15)
        return {"status": "success", "message": f"Container '{container_name}' restarted successfully."}
    except docker.errors.NotFound:
        return {"error": f"Container '{container_name}' not found."}
    except Exception as e:
        return {"error": f"Failed to restart container: {str(e)}"}

def get_docker_container_logs(container_name: str, lines: int = 30) -> dict:
    """Get the latest log lines from a specific container."""
    client = _get_docker_client()
    if not client:
        return {"error": "Cannot connect to Docker daemon."}
    
    lines = min(max(5, lines), 50)
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=lines, timestamps=True).decode("utf-8", errors="replace")
        return {
            "container": container_name,
            "lines": lines,
            "logs": logs.strip()
        }
    except docker.errors.NotFound:
        return {"error": f"Container '{container_name}' not found."}
    except Exception as e:
        return {"error": f"Failed to get logs: {str(e)}"}
