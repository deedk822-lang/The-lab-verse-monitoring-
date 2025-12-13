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
