import os
import asana

class AsanaClient:
    def __init__(self):
        self.access_token = os.getenv("ASANA_ACCESS_TOKEN")
        self.workspace_gid = os.getenv("ASANA_WORKSPACE_GID")
        self.available = bool(self.access_token and self.workspace_gid)
        self.client = asana.Client.access_token(self.access_token) if self.available else None

    def create_project(self, name):
        if not self.available:
            return {"gid": "mock_project_123"}
        return self.client.projects.create_project_for_workspace(self.workspace_gid, {"name": name})

    def create_task(self, project_gid, name):
        if not self.available:
            return {"gid": "mock_task_123"}
        return self.client.tasks.create_in_workspace(self.workspace_gid, {"projects": [project_gid], "name": name})
