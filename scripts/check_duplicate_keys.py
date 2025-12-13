import json
import sys

def check_duplicate_keys(pairs):
    keys = {}
    for key, value in pairs:
        if key in keys:
            print(f"❌ Duplicate key found: {key}")
            sys.exit(1)
        keys[key] = value
    return keys

try:
    with open('package.json', 'r') as f:
        json.load(f, object_pairs_hook=check_duplicate_keys)
    print("✅ No duplicate keys in package.json")
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON in package.json: {e}")
    sys.exit(1)
except FileNotFoundError:
    print("⚠️ package.json not found, skipping check.")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error checking package.json: {e}")
    sys.exit(1)
