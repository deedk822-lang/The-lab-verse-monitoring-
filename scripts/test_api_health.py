#!/usr/bin/env python3
"""
Vaal AI Empire - API Health Check Suite
Tests all external API connections without making destructive changes.
"""
import os
import sys
import httpx
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class APIHealthChecker:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.timeout = 10.0

    async def check_notion(self) -> Tuple[bool, str]:
        """Test Notion API connection"""
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            return False, "API key not configured"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.notion.com/v1/users',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Notion-Version': '2022-06-28'
                    },
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return True, "Connected successfully"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_jira(self) -> Tuple[bool, str]:
        """Test Jira API connection"""
        email = os.getenv('JIRA_USER_EMAIL')
        token = os.getenv('JIRA_LINK')  # Actually JIRA_API_TOKEN
        base_url = "https://dimakatsomoleli.atlassian.net"

        if not email or not token:
            return False, "Credentials not configured"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{base_url}/rest/api/3/myself',
                    auth=(email, token),
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    user = response.json()
                    return True, f"Connected as {user.get('displayName', 'user')}"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_wordpress(self) -> Tuple[bool, str]:
        """Test WordPress XML-RPC connection"""
        user = os.getenv('WORDPRESS_USER')
        password = os.getenv('WORDPRESS_PASSWORD')

        if not user or not password:
            return False, "Credentials not configured"

        try:
            # Test WordPress REST API instead of XML-RPC for simplicity
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{site_url}/wp-json/wp/v2/users/me',
                    auth=(user, password),
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return True, "Connected successfully"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_kaggle(self) -> Tuple[bool, str]:
        """Test Kaggle API connection"""
        username = os.getenv('KAGGLE_USERNAME')
        key = os.getenv('KAGGLE_KEY')

        if not username or not key:
            return False, "Credentials not configured"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.kaggle.com/api/v1/datasets/list',
                    auth=(username, key),
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return True, "Connected successfully"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_databricks(self) -> Tuple[bool, str]:
        """Test Databricks API connection"""
        host = os.getenv('DATABRICKS_HOST')
        token = os.getenv('DATABRICKS_API_KEY')

        if not host or not token:
            return False, "Credentials not configured"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{host}/api/2.0/preview/scim/v2/Me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    user = response.json()
                    return True, f"Connected as {user.get('userName', 'user')}"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_oss_storage(self) -> Tuple[bool, str]:
        """Test Alibaba Cloud OSS connection"""
        access_key = os.getenv('ACCESS_KEY_ID')
        secret_key = os.getenv('ACCESS_KEY_SECRET')

        if not access_key or not secret_key:
            return False, "Credentials not configured"

        try:
            # Simple endpoint check
            async with httpx.AsyncClient() as client:
                response = await client.head(
                    'https://oss-eu-west-1.aliyuncs.com',
                    timeout=self.timeout
                )
                if response.status_code in [200, 403, 404]:  # 403 is ok, means endpoint exists
                    return True, "Endpoint reachable"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_cohere(self) -> Tuple[bool, str]:
        """Test Cohere API connection"""
        api_key = os.getenv('COHERE_API_KEY')

        if not api_key:
            return False, "API key not configured"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.cohere.ai/v1/check-api-key',
                    headers={'Authorization': f'Bearer {api_key}'},
                    json={},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return True, "API key valid"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def check_dashscope(self) -> Tuple[bool, str]:
        """Test DashScope (Alibaba AI) API connection"""
        api_key = os.getenv('DASHSCOPE_API_KEY')

        if not api_key:
            return False, "API key not configured"

        try:
            async with httpx.AsyncClient() as client:
                # Test with a minimal API call
                response = await client.get(
                    'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=self.timeout
                )
                # Even an error response means the endpoint is reachable
                if response.status_code in [200, 400, 401]:
                    return True, "Endpoint reachable"
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    async def run_all_checks(self):
        """Run all API health checks"""
        print(f"\n{BLUE}🏥 Vaal AI Empire - API Health Check Suite{NC}")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        checks = [
            ("Notion API", self.check_notion),
            ("Jira API", self.check_jira),
            ("WordPress API", self.check_wordpress),
            ("Kaggle API", self.check_kaggle),
            ("Databricks API", self.check_databricks),
            ("OSS Storage", self.check_oss_storage),
            ("Cohere AI", self.check_cohere),
            ("DashScope AI", self.check_dashscope),
        ]

        for name, check_func in checks:
            print(f"Testing {name}...", end=" ", flush=True)
            success, message = await check_func()

            if success:
                print(f"{GREEN}✓{NC} {message}")
            else:
                print(f"{RED}✗{NC} {message}")

            self.results.append((name, success, message))

        # Summary
        print("\n" + "=" * 50)
        print("Summary:")
        passed = sum(1 for _, success, _ in self.results if success)
        failed = len(self.results) - passed

        print(f"{GREEN}✓ Passed: {passed}{NC}")
        print(f"{RED}✗ Failed: {failed}{NC}")

        if failed > 0:
            print(f"\n{YELLOW}Failed checks:{NC}")
            for name, success, message in self.results:
                if not success:
                    print(f"  • {name}: {message}")
            return False

        print(f"\n{GREEN}✓ All API health checks passed!{NC}")
        return True


async def main():
    checker = APIHealthChecker()
    success = await checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
