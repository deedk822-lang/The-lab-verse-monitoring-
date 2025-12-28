import os
import sys
import importlib.util

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def check_env_var(name, required=True):
    value = os.getenv(name)
    if value:
        print(f"{Colors.GREEN}✅{Colors.END} {name}: Set")
        return True
    else:
        symbol = f"{Colors.RED}❌" if required else f"{Colors.YELLOW}⚠️"
        status = "REQUIRED" if required else "Optional"
        print(f"{symbol}{Colors.END} {name}: Missing ({status})")
        return not required

def check_file(path):
    if os.path.exists(path):
        print(f"{Colors.GREEN}✅{Colors.END} {path}: Found")
        return True
    else:
        print(f"{Colors.RED}❌{Colors.END} {path}: Missing")
        return False

def check_module(name):
    spec = importlib.util.find_spec(name)
    if spec:
        print(f"{Colors.GREEN}✅{Colors.END} Module {name}: Importable")
        return True
    else:
        print(f"{Colors.RED}❌{Colors.END} Module {name}: Not found")
        return False

def main():
    print("🔍 Validating Lab Verse Monitoring Environment\n")

    all_good = True

    # Check required environment variables
    print("📋 Environment Variables:")
    all_good &= check_env_var("API_KEY", required=True)
    all_good &= check_env_var("LOCALAI_ENDPOINT", required=True)
    all_good &= check_env_var("DATABASE_URL", required=False)
    all_good &= check_env_var("REDIS_URL", required=False)

    print("\n📁 Critical Files:")
    all_good &= check_file("rainmaker_orchestrator.py")
    all_good &= check_file("api/server.py")
    all_good &= check_file("requirements.txt")
    all_good &= check_file("Dockerfile")

    print("\n📦 Python Modules:")
    all_good &= check_module("fastapi")
    all_good &= check_module("uvicorn")
    all_good &= check_module("httpx")

    print("\n" + "="*50)
    if all_good:
        print(f"{Colors.GREEN}✅ All validations passed!{Colors.END}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}❌ Some validations failed - see above{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
