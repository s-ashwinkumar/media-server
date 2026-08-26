import shutil
import psutil
from pathlib import Path
from config import MONITORED_PATHS

def get_disk_space() -> list[dict]:
    """Check free and total disk space across media storage and OS partitions."""
    results = []
    seen_mounts = set()
    
    for label, path_str in MONITORED_PATHS.items():
        p = Path(path_str)
        if not p.exists():
            continue
        try:
            usage = shutil.disk_usage(p)
            total_gb = round(usage.total / (1024**3), 1)
            used_gb = round(usage.used / (1024**3), 1)
            free_gb = round(usage.free / (1024**3), 1)
            percent_used = round((usage.used / usage.total) * 100, 1)
            
            # Avoid repeating the same mount point
            mount_id = f"{total_gb}_{used_gb}"
            if mount_id in seen_mounts and label != "Root (OS)":
                continue
            seen_mounts.add(mount_id)
            
            results.append({
                "storage_pool": label,
                "path": str(p),
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent_used": f"{percent_used}%"
            })
        except Exception as e:
            results.append({"storage_pool": label, "error": str(e)})
            
    return results

def get_system_stats() -> dict:
    """Get current server CPU usage, memory utilization, and hardware temperatures."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        
        temps = {}
        try:
            raw_temps = psutil.sensors_temperatures()
            for name, entries in raw_temps.items():
                if entries:
                    temps[name] = f"{entries[0].current}°C"
        except Exception:
            temps = "Sensors unavailable"
        
        return {
            "cpu_usage_percent": f"{cpu_percent}%",
            "memory_total_gb": round(mem.total / (1024**3), 1),
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_free_gb": round(mem.available / (1024**3), 1),
            "memory_percent": f"{mem.percent}%",
            "temperatures": temps
        }
    except Exception as e:
        return {"error": f"Failed to get system stats: {str(e)}"}
