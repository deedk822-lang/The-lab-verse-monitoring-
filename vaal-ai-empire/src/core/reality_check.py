import os
import sys
import logging

logger = logging.getLogger("RealityCheck")

def ensure_production_ready():
    """
    CRASHES the system if it detects a simulation environment.
    """
    # 1. Check Critical Keys
    required_keys = [
        "DASHSCOPE_API_KEY", # Qwen
        "OSS_ACCESS_KEY_ID", # Alibaba Storage
        "JIRA_API_TOKEN"     # Reporting
    ]

    missing = [k for k in required_keys if not os.getenv(k)]

    if missing:
        logger.error(f"❌ REALITY CHECK FAILED: Missing Keys {missing}")
        logger.error("   The system refuses to run in Mock Mode. Export these keys.")
        sys.exit(1)

    # 2. Check Network (Ping Alibaba)
    # We don't just assume internet; we verify we can reach the brain.
    import requests
    try:
        # Ping Alibaba DNS/Endpoint
        requests.get("https://oss-eu-west-1.aliyuncs.com", timeout=2)
    except:
        logger.error("❌ REALITY CHECK FAILED: Cannot reach Alibaba Cloud.")
        sys.exit(1)

    logger.info("✅ REALITY CHECK PASSED. SYSTEM IS LIVE.")
