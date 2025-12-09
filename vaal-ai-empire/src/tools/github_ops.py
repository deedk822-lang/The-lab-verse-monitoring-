import os
import logging
from github import Github
from qwen_agent.tools.base import BaseTool, register_tool

logger = logging.getLogger("GitHubOps")

@register_tool('github_omniscience')
class GitHubOmniscience(BaseTool):
    description = 'Allows Qwen to list files, read code, and fix bugs in the repository.'
    parameters = [
        {'name': 'action', 'type': 'string', 'description': 'list_files | read_file | update_file', 'required': True},
        {'name': 'path', 'type': 'string', 'description': 'File path in repo (e.g., src/agents/tax_collector.py)', 'required': False},
        {'name': 'content', 'type': 'string', 'description': 'New content for update_file', 'required': False}
    ]

    def __init__(self):
        # The Master Key
        self.token = os.getenv("PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPOSITORY") # e.g. "deedk822-lang/The-lab-verse-monitoring-"

        if self.token:
            self.g = Github(self.token)
            # If repo name isn't set (local run), default to current folder context or fail gracefully
            try:
                self.repo = self.g.get_repo(self.repo_name) if self.repo_name else None
            except:
                self.repo = None

    def call(self, params: str, **kwargs) -> str:
        if not self.token or not self.repo:
            return "❌ GitHub Tool Offline. (Check PERSONAL_ACCESS_TOKEN and GITHUB_REPOSITORY env vars)"

        # Parse JSON params from Qwen
        import json
        try:
            p = json.loads(params)
        except:
            return "Invalid Parameters"

        action = p.get('action')
        path = p.get('path')

        try:
            # ACTION 1: LOCATE MISSING FILES
            if action == 'list_files':
                contents = self.repo.get_contents(path if path else "")
                files = [c.path for c in contents]
                return str(files)

            # ACTION 2: READ BROKEN CODE
            if action == 'read_file':
                content = self.repo.get_contents(path).decoded_content.decode()
                return content

            # ACTION 3: FIX BUGS (SELF-HEALING)
            if action == 'update_file':
                new_content = p.get('content')
                contents = self.repo.get_contents(path)
                self.repo.update_file(contents.path, "fix: qwen auto-repair", new_content, contents.sha)
                return f"✅ Successfully patched {path}"

        except Exception as e:
            return f"GitHub Error: {e}"

        return "Unknown Action"
