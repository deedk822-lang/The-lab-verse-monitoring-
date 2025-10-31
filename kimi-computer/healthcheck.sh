#!/bin/bash
# healthcheck.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the URL to check.
URL="http://localhost:8080/health"

# Use curl to make the request.
# -f: Fail silently (no output at all) on HTTP errors (4xx and 5xx).
# -s: Silent or quiet mode. Don't show progress meter or error messages.
# -o /dev/null: Redirect the body of the response to /dev/null, as we are only interested in the exit code.
if curl -fs -o /dev/null "$URL"; then
  echo "Health check passed."
  exit 0
else
  echo "Health check failed."
  exit 1
fi
