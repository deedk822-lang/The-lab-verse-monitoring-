#!/bin/bash
set -e

echo "🧱 ACTIVATING DATABRICKS CONNECTION..."
echo "   - Host: https://dbc-623dbd3c-abd3.cloud.databricks.com"
echo "   - Key Source: DATABRICKS_API_KEY (Existing)"

# 1. CONFIGURE ENVIRONMENT
# We map your existing secret name to what the SDK expects.
export DATABRICKS_HOST="https://dbc-623dbd3c-abd3.cloud.databricks.com"

if [ -z "$DATABRICKS_API_KEY" ]; then
    echo "⚠️  DATABRICKS_API_KEY is not set in your current shell."
    echo "   Action: Please run: export DATABRICKS_API_KEY='dapi...'"
    exit 1
else
    # The Mapping Step
    export DATABRICKS_TOKEN="$DATABRICKS_API_KEY"
    echo "✅ Key detected and mapped."
fi

# 2. SAVE TO .ENV (For persistence)
sed -i '/DATABRICKS_HOST/d' vaal-ai-empire/.env
sed -i '/DATABRICKS_TOKEN/d' vaal-ai-empire/.env

echo "DATABRICKS_HOST=$DATABRICKS_HOST" >> vaal-ai-empire/.env
echo "DATABRICKS_TOKEN=$DATABRICKS_API_KEY" >> vaal-ai-empire/.env

# 3. INSTALL DRIVER
pip install databricks-sdk --upgrade --quiet

# 4. VERIFY CONNECTION
# We attempt to fetch the workspace status.

cat << 'EOF' > vaal-ai-empire/scripts/verify_databricks.py
import os
import logging
from databricks.sdk import WorkspaceClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("Databricks")

def check_pulse():
    try:
        w = WorkspaceClient()
        # Simple call to check identity
        me = w.current_user.me()
        logger.info(f"✅ CONNECTION SUCCESSFUL.")
        logger.info(f"   - User: {me.user_name}")
        logger.info(f"   - Active: {me.active}")
    except Exception as e:
        logger.error(f"❌ Connection Failed: {e}")
        logger.error("   - Check if your Token has expired.")
        exit(1)

if __name__ == "__main__":
    check_pulse()
EOF

python3 vaal-ai-empire/scripts/verify_databricks.py
