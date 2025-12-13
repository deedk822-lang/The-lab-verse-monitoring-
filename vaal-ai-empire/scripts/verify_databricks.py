import os
import logging
from databricks.sdk import WorkspaceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabricksConnect")

def verify_access():
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        logger.error("❌ Credentials missing. Run the connection script again.")
        return

    logger.info(f"🔌 Connecting to {host}...")

    try:
        w = WorkspaceClient(host=host, token=token)

        # Test 1: Get Current User
        user = w.current_user.me()
        logger.info(f"   ✅ Authenticated as: {user.user_name}")

        # Test 2: List Clusters (Compute)
        clusters = list(w.clusters.list())
        logger.info(f"   ✅ Visible Clusters: {len(clusters)}")
        for c in clusters[:3]:
            logger.info(f"      - {c.cluster_name} ({c.state})")

    except Exception as e:
        logger.error(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_access()
