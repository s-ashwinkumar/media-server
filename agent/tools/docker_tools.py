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

import subprocess
from pathlib import Path

COMPOSE_DIR = Path(__file__).resolve().parent.parent.parent / "compose_files"

def update_docker_container(service_name: str) -> dict:
    """Pull the latest image and recreate a container service using Docker Compose."""
    client = _get_docker_client()
    if not client:
        return {"error": "Cannot connect to Docker daemon."}

    # Verify container exists
    try:
        client.containers.get(service_name)
    except docker.errors.NotFound:
        return {"error": f"Container '{service_name}' not found."}

    cmd = f"docker compose pull {service_name} && docker compose up -d {service_name}"
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(COMPOSE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300
        )
        if proc.returncode == 0:
            return {
                "status": "success",
                "message": f"Successfully updated and recreated `{service_name}`.",
                "output": proc.stdout[-500:] if proc.stdout else ""
            }
        else:
            return {
                "error": f"Failed to update `{service_name}` (exit code {proc.returncode}):\n{proc.stdout[-500:]}"
            }
    except subprocess.TimeoutExpired:
        return {"error": f"Updating `{service_name}` timed out after 5 minutes."}
    except Exception as e:
        return {"error": f"Failed to run update command: {str(e)}"}

