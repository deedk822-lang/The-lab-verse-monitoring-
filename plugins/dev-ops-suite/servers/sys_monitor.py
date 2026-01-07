import sys
import psutil
import subprocess
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("system-doctor")

@mcp.tool()
def get_resource_usage() -> str:
    """Returns real-time CPU, Memory, and Disk usage."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return json.dumps({
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_available_gb": round(mem.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }, indent=2)
    except Exception as e:
        return f"Error reading resources: {str(e)}"

@mcp.tool()
def check_service_status(service_name: str) -> str:
    """Checks if a system service (e.g., docker, nginx) is active."""
    try:
        # Cross-platform check
        if sys.platform == "darwin" or sys.platform == "linux":
            result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True)
            if result.returncode == 0:
                return f"✅ {service_name} is RUNNING"

            # Fallback for Docker specifically if systemctl fails
            if service_name == "docker":
                docker_check = subprocess.run(["docker", "info"], capture_output=True)
                if docker_check.returncode == 0:
                    return "✅ Docker is RUNNING (Verified via daemon)"

            return f"❌ {service_name} is INACTIVE or NOT FOUND"
    except Exception as e:
        return f"Error checking service: {str(e)}"

@mcp.tool()
def list_listening_ports() -> str:
    """Lists local ports currently in use (good for debugging conflicts)."""
    connections = psutil.net_connections(kind='inet')
    listening = [c for c in connections if c.status == 'LISTEN']

    ports = []
    for c in listening[:10]: # Limit to top 10 to avoid token overflow
        ports.append(f"Port {c.laddr.port} (PID: {c.pid})")

    return "\n".join(ports)

if __name__ == "__main__":
    mcp.run()
