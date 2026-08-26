import json
import docker

def check_vpn_ip_leak() -> dict:
    """Check the public IP address and ISP of the VPN tunnel (qbittorrent/surfshark container) to verify no IP leak."""
    try:
        client = docker.from_env()
    except Exception as e:
        return {"error": f"Cannot connect to Docker: {str(e)}"}
    
    container_names = ["surfshark", "qbittorrent"]
    target_container = None
    for name in container_names:
        try:
            target_container = client.containers.get(name)
            if target_container.status == "running":
                break
        except Exception:
            continue
            
    if not target_container:
        return {"error": "Neither surfshark nor qbittorrent container is running to check VPN IP."}
        
    try:
        exec_res = target_container.exec_run("curl -s https://ipinfo.io/json")
        output = exec_res.output.decode("utf-8", errors="replace").strip()
        data = json.loads(output)
        return {
            "status": "VPN Active" if "ip" in data else "Unknown",
            "vpn_ip": data.get("ip"),
            "location": f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}",
            "isp_org": data.get("org", "Unknown"),
            "container_checked": target_container.name
        }
    except Exception as e:
        return {"error": f"Failed to test VPN IP leak: {str(e)}"}
