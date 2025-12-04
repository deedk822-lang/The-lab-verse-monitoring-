import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AsanaClient:
    def __init__(self):
        try:
            import asana
            self.asana = asana
        except ImportError:
            raise ImportError("Asana SDK not installed. Please install it with 'pip install asana'")

        token = os.getenv("ASANA_ACCESS_TOKEN")
        if not token:
            raise ValueError("ASANA_ACCESS_TOKEN environment variable not set.")

        self.client = asana.Client.access_token(token)
        self.workspace = os.getenv("ASANA_WORKSPACE_GID")
        if not self.workspace:
            logger.warning("ASANA_WORKSPACE_GID is not set. Some project creation features may not work as expected.")

    def create_project(self, name: str) -> Dict:
        """Create project for client"""
        if not self.workspace:
            raise ValueError("Cannot create project: ASANA_WORKSPACE_GID is not set.")
        try:
            return self.client.projects.create({
                "name": name,
                "workspace": self.workspace,
                "notes": "Managed by Vaal AI Empire"
            })
        except Exception as e:
            logger.error(f"Asana error: {e}")
            raise e

    def create_task(self, project_id: str, name: str) -> Dict:
        """Create task in project"""
        if not self.workspace:
            raise ValueError("Cannot create task: ASANA_WORKSPACE_GID is not set.")
        try:
            return self.client.tasks.create({
                "name": name,
                "projects": [project_id],
                "workspace": self.workspace
            })
        except Exception as e:
            logger.error(f"Asana error: {e}")
            raise e
