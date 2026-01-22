import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ⚡ Bolt Optimization: Centralized session for connection pooling
# This shared session object allows for reusing TCP connections, which significantly
# reduces latency for repeated API calls to the same host.

# Configure retry strategy for resilience
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
)

# Mount the retry strategy to the session
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Set a reasonable timeout for all requests
http.timeout = 15
