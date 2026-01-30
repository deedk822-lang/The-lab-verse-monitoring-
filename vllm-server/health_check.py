# health_check.py
import requests


def check_kimi_health():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Kimi Linear is healthy")
            return True
    except Exception:
        print("✗ Kimi Linear is unreachable")
        return False
