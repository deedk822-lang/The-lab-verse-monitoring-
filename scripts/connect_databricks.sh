#!/bin/bash
set -e

echo "🧱 CONNECTING DATABRICKS NODE..."
echo "   - Host: https://dbc-623dbd3c-abd3.cloud.databricks.com"
echo "   - User: deedk822@gmail.com"

# 1. SET ENVIRONMENT VARIABLES
# We use the specific URL you provided.
export DATABRICKS_HOST="https://dbc-623dbd3c-abd3.cloud.databricks.com"

# 2. ASK FOR THE TOKEN (Secure Input)
if [ -z "$DATABRICKS_TOKEN" ]; then
    echo "🔑 ENTER YOUR DATABRICKS TOKEN (dapi...):"
    read -s DATABRICKS_TOKEN
    export DATABRICKS_TOKEN
fi

# 3. PERSIST CONFIGURATION
# We save these to the .env file so the Agent remembers them.
sed -i '/DATABRICKS_HOST/d' vaal-ai-empire/.env
sed -i '/DATABRICKS_TOKEN/d' vaal-ai-empire/.env

echo "DATABRICKS_HOST=$DATABRICKS_HOST" >> vaal-ai-empire/.env
echo "DATABRICKS_TOKEN=$DATABRICKS_TOKEN" >> vaal-ai-empire/.env

# 4. INSTALL DRIVER
pip install databricks-sdk --upgrade --quiet

# 5. VERIFY CONNECTION (The "Handshake")
# We try to list clusters to prove we are inside the system.

cat << 'EOF' > vaal-ai-empire/scripts/verify_databricks.py
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
EOF

python3 vaal-ai-empire/scripts/verify_databricks.py

echo "✅ DATABRICKS NODE LINKED."
