import time
import sys

print("Revenue Notification Worker Started.")
print("Monitoring OSS for Revenue Triggers...")

try:
    while True:
        # This is where the actual OSS polling logic would go.
        # For now, we'll just sleep to simulate a background task.
        print("...")
        time.sleep(60)
except KeyboardInterrupt:
    print("\nShutting down Revenue Notification Worker.")
    sys.exit(0)
