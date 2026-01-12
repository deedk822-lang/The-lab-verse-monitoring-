import os
import asyncio
import json
import logging
from typing import Dict, List, Any, Set

import aiohttp
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubMonitorSensor:
    """
    Monitors GitHub repositories for new commits containing specific keywords
    and publishes findings to a Redis channel.
    """
    def __init__(self, config: Dict[str, Any], redis_client: redis.Redis):
        self.config = config['sensors']['github_monitor']
        self.redis_client = redis_client
        self.redis_channel = config['redis']['events_channel']
        self.api_token = os.getenv("GITHUB_API_TOKEN") # For higher rate limits
        self.processed_commits: Set[str] = set()

    async def _get_latest_commits(self, session: aiohttp.ClientSession, repo: str) -> List[Dict[str, Any]]:
        """Fetches the latest commits for a single repository."""
        url = f"https://api.github.com/repos/{repo}/commits"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching commits for {repo}: {e}")
            return []

    async def _process_commits(self, commits: List[Dict[str, Any]], repo: str):
        """Filters commits and publishes events for new, relevant ones."""
        keywords = {k.lower() for k in self.config['keywords']}

        for commit_data in commits:
            sha = commit_data.get('sha')
            if not sha or sha in self.processed_commits:
                continue

            self.processed_commits.add(sha) # Mark as processed immediately

            message = commit_data.get('commit', {}).get('message', '').lower()

            if any(keyword in message for keyword in keywords):
                event_payload = {
                    "source": "github_monitor",
                    "event_type": "new_commit",
                    "metadata": {
                        "repository": repo,
                        "commit_hash": sha,
                        "commit_message": commit_data.get('commit', {}).get('message'),
                        "author": commit_data.get('commit', {}).get('author', {}).get('name'),
                        "url": commit_data.get('html_url')
                    }
                }
                logger.info(f"Publishing new relevant commit from {repo}: {sha[:7]}")
                await self.redis_client.publish(self.redis_channel, json.dumps(event_payload))

    async def run(self):
        """Main loop to periodically poll GitHub repositories."""
        logger.info("Starting GitHub Monitor Sensor...")
        async with aiohttp.ClientSession() as session:
            while True:
                logger.info("Polling for new commits...")
                tasks = [
                    self._get_latest_commits(session, repo)
                    for repo in self.config['repositories']
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, repo_commits in enumerate(results):
                    repo_name = self.config['repositories'][i]
                    if isinstance(repo_commits, list):
                        await self._process_commits(repo_commits, repo_name)
                    else:
                        logger.error(f"Skipping processing for {repo_name} due to fetch error: {repo_commits}")

                logger.info(f"Poll cycle complete. Waiting for {self.config['poll_interval']} seconds.")
                await asyncio.sleep(self.config['poll_interval'])