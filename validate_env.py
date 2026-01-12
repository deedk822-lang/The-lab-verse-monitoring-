import os
import sys

# Fail fast if dependencies are missing
try:
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Python Dependency Error: {e}")
    print("Run: pip install requests python-dotenv anthropic")
    sys.exit(1)

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
NC = '\033[0m'

def log_success(msg): print(f"{GREEN}✓ {msg}{NC}")
def log_fail(msg): print(f"{RED}✗ {msg}{NC}")

def check_anthropic_connectivity():
    """Verifies the Anthropic API (The New Brain) is reachable."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return False, "ANTHROPIC_API_KEY missing"

    try:
        # Minimal probe to verify key validity without spending many tokens
        # We manually construct a request to avoid needing the full SDK just for validation
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Listing models is a cheap way to verify auth
        resp = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=5)

        if resp.status_code == 200:
            return True, "Anthropic Brain Online"
        elif resp.status_code == 401:
            return False, "Anthropic API Key Invalid (401)"
        return False, f"Anthropic API Error: {resp.status_code}"
    except Exception as e:
        return False, f"Anthropic Unreachable: {str(e)}"

def main():
    print("🔍 Starting Deep Environment Validation...")
    has_error = False

    # 1. Connectivity Check (Anthropic)
    ok, msg = check_anthropic_connectivity()
    if ok:
        log_success(msg)
    else:
        log_fail(msg); has_error = True

    # 2. Variable Check (Grafana)
    if not os.getenv("GRAFANA_WEBHOOK_URL"):
        log_fail("GRAFANA_WEBHOOK_URL missing")
        # has_error = True # Optional: Uncomment to block deploy on missing metrics
    else:
        log_success("Grafana Webhook Configured")

    if has_error:
        print(f"\n{RED}Validation Failed. Aborting Deployment.{NC}")
        sys.exit(1)

    print(f"{GREEN}Environment Verified. Ready for Lift-off.{NC}")
    sys.exit(0)

if __name__ == "__main__":
    main()
