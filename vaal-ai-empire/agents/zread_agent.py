"""
Vaal AI Empire - Zread MCP Agent (Private Repository Intelligence)

Capabilities:
- Atomic search (find specific files, functions, classes)
- Deep reading (full file content with context)
- Repository structure analysis (tree view, module understanding)
"""

import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ZreadAgent:
    """
    Agent for interacting with Zread MCP (Private Repo Intelligence).
    """

    def __init__(self, zai_api_key: str = None):
        self.api_key = zai_api_key or os.getenv('ZAI_API_KEY')
        if not self.api_key:
            raise ValueError("ZAI_API_KEY environment variable not set.")
        self.base_url = os.getenv('ZREAD_API_BASE', "https://api.z.ai/api/mcp/zread/mcp")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_repo(self, repo_url: str, query: str, path_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search for code/files in a private repository using Zread MCP.

        Args:
            repo_url: Full GitHub URL (e.g., https://github.com/user/repo)
            query: Search query (e.g., "billing logic bug")
            path_filter: Optional filter (e.g., "src/", "server/")

        Returns:
            A list of dictionaries, where each dictionary represents a match.
        """
        prompt = f"""
        You are a specialized code search assistant. Your goal is to find the following in the repository '{repo_url}':

        Query: {query}
        {f'Path Filter: {path_filter}' if path_filter else 'None'}

        Return:
        - List of matching files/directories.
        - For code files, return the first 50 lines.
        - For directories, return the directory structure.
        - Return relevant code snippets around matches.

        Focus on:
        - Billing logic (Stripe, PayPal)
        - Database schemas (SQL, NoSQL)
        - API endpoints (Express, Flask)
        - Authentication logic (OAuth, JWT)
        - Security vulnerabilities (SQL injection, XSS)
        """

        data = {
            "messages": [
                {"role": "system", "content": prompt}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, data=json.dumps(data), timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return []

    def get_repo_structure(self, repo_url: str) -> Dict[str, Any]:
        """
        Get the tree structure of a repository.
        """
        data = {
            "messages": [
                {"role": "user", "content": f"Get the directory tree structure for '{repo_url}'."}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, data=json.dumps(data), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {}

    def read_specific_file(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """
        Read the full content of a specific file.
        """
        data = {
            "messages": [
                {"role": "user", "content": f"Read the full content of the file '{file_path}' in the repository '{repo_url}'."}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, data=json.dumps(data), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}
