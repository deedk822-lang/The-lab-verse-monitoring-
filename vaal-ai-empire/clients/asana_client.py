import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AsanaClient:
    def __init__(self):
        try:
            import asana
            self.asana = asana
            token = os.getenv("ASANA_ACCESS_TOKEN")

            if token:
                self.client = asana.Client.access_token(token)
                self.workspace = os.getenv("ASANA_WORKSPACE_GID")
                self.available = True
            else:
                logger.warning("ASANA_ACCESS_TOKEN not set - using mock mode")
                self.available = False
        except ImportError:
            logger.warning("Asana SDK not installed - using mock mode")
            self.available = False

    def create_project(self, name: str) -> Dict:
        """Create project for client"""
        if not self.available:
            return {
                "gid": f"mock_project_{name.replace(' ', '_')}",
                "name": name
            }

        try:
            return self.client.projects.create({
                "name": name,
                "workspace": self.workspace,
                "notes": "Managed by Vaal AI Empire"
            })
        except Exception as e:
            logger.error(f"Asana error: {e}")
            return {"error": str(e), "gid": "error"}

    def create_task(self, project_id: str, name: str) -> Dict:
        """Create task in project"""
        if not self.available:
            return {
                "gid": f"mock_task_{name.replace(' ', '_')}",
                "name": name
            }

        try:
            return self.client.tasks.create({
                "name": name,
                "projects": [project_id],
                "workspace": self.workspace
            })
        except Exception as e:
            logger.error(f"Asana error: {e}")
            return {"error": str(e), "gid": "error"}
