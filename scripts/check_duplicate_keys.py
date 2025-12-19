
import json
import sys
import os

def check_duplicate_keys(pairs):
    keys = {}
    for key, value in pairs:
        if key in keys:
            print(f"❌ Duplicate key found: {key}", file=sys.stderr)
            sys.exit(1)
        keys[key] = value
    return keys

def main():
    if not os.path.exists('package.json'):
        print("⚠️ package.json not found (skipping check)")
        sys.exit(0)

    try:
        with open('package.json', 'r') as f:
            json.load(f, object_pairs_hook=check_duplicate_keys)
        print("✅ No duplicate keys in package.json")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in package.json: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking package.json: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
