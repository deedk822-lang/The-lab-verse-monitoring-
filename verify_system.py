#!/usr/bin/env python3
"""
Lab-Verse Complete System Verification
Tests all integrations, webhooks, and functionality
"""
import asyncio
import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
import httpx
from datetime import datetime
import json

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    message: str
    duration_ms: float


class SystemVerification:
    """Complete system verification"""

    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.client = httpx.AsyncClient(timeout=30.0)

    def print_header(self):
        """Print verification header"""
        print("═" * 70)
        print("  LAB-VERSE MONITORING SYSTEM - COMPLETE VERIFICATION")
        print("═" * 70)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print("═" * 70)
        print()

    def print_category(self, category: str):
        """Print category header"""
        print(f"\n{BLUE}{'═' * 70}{RESET}")
        print(f"{BLUE}  {category}{RESET}")
        print(f"{BLUE}{'═' * 70}{RESET}")

    def print_result(self, result: TestResult):
        """Print test result"""
        status = f"{GREEN}✓ PASS{RESET}" if result.passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} | {result.name}")
        print(f"      {result.message} ({result.duration_ms:.2f}ms)")

    async def test_infrastructure(self):
        """Test infrastructure services"""
        self.print_category("INFRASTRUCTURE TESTS")

        # Test main health endpoint
        await self._test_endpoint(
            name="Main Health Endpoint",
            category="infrastructure",
            method="GET",
            endpoint="/health"
        )

        # Test API health
        await self._test_endpoint(
            name="API Health Endpoint",
            category="infrastructure",
            method="GET",
            endpoint="/api/health"
        )

        # Test integration health
        await self._test_endpoint(
            name="Integration Health Status",
            category="infrastructure",
            method="GET",
            endpoint="/health/integrations"
        )

    async def test_platform_integrations(self):
        """Test all platform integrations"""
        self.print_category("PLATFORM INTEGRATION TESTS")

        platforms = [
            ("Grafana Dashboards", "/api/grafana/dashboards"),
            ("Grafana Alerts", "/api/grafana/alerts"),
            ("Hugging Face Spaces", "/api/huggingface/spaces"),
            ("Hugging Face Models", "/api/huggingface/models"),
            ("DataDog Monitors", "/api/datadog/monitors"),
            ("DataDog Pipelines", "/api/datadog/pipelines"),
            ("HubSpot Contacts", "/api/hubspot/contacts?limit=10"),
            ("HubSpot Deals", "/api/hubspot/deals?limit=10"),
            ("Confluence Spaces", "/api/confluence/spaces"),
            ("ClickUp Spaces", "/api/clickup/spaces"),
            ("CodeRabbit Metrics", "/api/coderabbit/metrics"),
        ]

        for name, endpoint in platforms:
            await self._test_endpoint(
                name=name,
                category="platform",
                method="GET",
                endpoint=endpoint
            )

    async def test_webhooks(self):
        """Test webhook endpoints"""
        self.print_category("WEBHOOK TESTS")

        webhooks = [
            ("Grafana Webhook", "/webhooks/grafana", {"title": "Test", "state": "ok"}),
            ("HubSpot Webhook", "/webhooks/hubspot", {"subscriptionType": "test"}),
            ("ClickUp Webhook", "/webhooks/clickup", {"event": "test"}),
        ]

        for name, endpoint, payload in webhooks:
            await self._test_endpoint(
                name=name,
                category="webhook",
                method="POST",
                endpoint=endpoint,
                json=payload
            )

    async def test_unified_endpoints(self):
        """Test unified dashboard endpoints"""
        self.print_category("UNIFIED DASHBOARD TESTS")

        # Test dashboard summary
        await self._test_endpoint(
            name="Dashboard Summary",
            category="unified",
            method="GET",
            endpoint="/api/dashboard/summary"
        )

        # Test sync endpoint
        await self._test_endpoint(
            name="Platform Sync",
            category="unified",
            method="POST",
            endpoint="/api/sync",
            json={"platforms": []}
        )

    async def test_security(self):
        """Test security features"""
        self.print_category("SECURITY TESTS")

        # Test CORS headers
        start = datetime.now()
        try:
            response = await self.client.options(
                f"{self.base_url}/api/health",
                headers={"Origin": "https://test.com"}
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            cors_header = response.headers.get("Access-Control-Allow-Origin", "")
            passed = cors_header != "" or response.status_code == 200

            self.results.append(TestResult(
                name="CORS Configuration",
                category="security",
                passed=passed,
                message=f"CORS header: {cors_header or 'Not set'}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self.results.append(TestResult(
                name="CORS Configuration",
                category="security",
                passed=False,
                message=f"Error: {str(e)}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

    async def test_performance(self):
        """Test system performance"""
        self.print_category("PERFORMANCE TESTS")

        # Test response time
        start = datetime.now()
        try:
            response = await self.client.get(f"{self.base_url}/health")
            duration = (datetime.now() - start).total_seconds() * 1000

            passed = duration < 500  # Should be under 500ms

            self.results.append(TestResult(
                name="API Response Time",
                category="performance",
                passed=passed,
                message=f"Response time: {duration:.2f}ms (target: <500ms)",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self.results.append(TestResult(
                name="API Response Time",
                category="performance",
                passed=False,
                message=f"Error: {str(e)}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        # Test concurrent requests
        await self._test_concurrent_requests()

    async def _test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        start = datetime.now()
        try:
            tasks = [
                self.client.get(f"{self.base_url}/health")
                for _ in range(10)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            duration = (datetime.now() - start).total_seconds() * 1000

            success_count = sum(
                1 for r in responses
                if not isinstance(r, Exception) and r.status_code == 200
            )

            passed = success_count >= 8  # 80% success rate

            self.results.append(TestResult(
                name="Concurrent Request Handling",
                category="performance",
                passed=passed,
                message=f"{success_count}/10 requests succeeded",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self.results.append(TestResult(
                name="Concurrent Request Handling",
                category="performance",
                passed=False,
                message=f"Error: {str(e)}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

    async def _test_endpoint(
        self,
        name: str,
        category: str,
        method: str,
        endpoint: str,
        **kwargs
    ):
        """Test a single endpoint"""
        start = datetime.now()
        try:
            url = f"{self.base_url}{endpoint}"
            response = await self.client.request(method, url, **kwargs)
            duration = (datetime.now() - start).total_seconds() * 1000

            passed = response.status_code in [200, 201, 202]
            message = f"Status: {response.status_code}"

            # Check for data in response
            if passed and method == "GET":
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        message += f" | Keys: {', '.join(keys)}"
                except:
                    pass

            self.results.append(TestResult(
                name=name,
                category=category,
                passed=passed,
                message=message,
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        except httpx.HTTPStatusError as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self.results.append(TestResult(
                name=name,
                category=category,
                passed=False,
                message=f"HTTP {e.response.status_code}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self.results.append(TestResult(
                name=name,
                category=category,
                passed=False,
                message=f"Error: {str(e)[:50]}",
                duration_ms=duration
            ))
            self.print_result(self.results[-1])

    def print_summary(self):
        """Print verification summary"""
        print(f"\n{'═' * 70}")
        print(f"  VERIFICATION SUMMARY")
        print(f"{'═' * 70}")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"passed": 0, "failed": 0}
            if result.passed:
                categories[result.category]["passed"] += 1
            else:
                categories[result.category]["failed"] += 1

        print(f"\nOverall Results:")
        print(f"  Total Tests:   {total}")
        print(f"  {GREEN}Passed:        {passed} ({passed/total*100:.1f}%){RESET}")
        print(f"  {RED}Failed:        {failed} ({failed/total*100:.1f}%){RESET}")

        print(f"\nResults by Category:")
        for category, stats in categories.items():
            total_cat = stats["passed"] + stats["failed"]
            pass_rate = stats["passed"] / total_cat * 100 if total_cat > 0 else 0
            color = GREEN if pass_rate >= 80 else YELLOW if pass_rate >= 50 else RED
            print(f"  {category.title():20} {color}{stats['passed']}/{total_cat} passed ({pass_rate:.1f}%){RESET}")

        # Show failed tests
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in failed_tests:
                print(f"  ✗ {result.name}")
                print(f"    {result.message}")

        print(f"\n{'═' * 70}")

        # Overall status
        if failed == 0:
            print(f"{GREEN}✓ ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL{RESET}")
            return 0
        elif failed <= total * 0.2:  # 80%+ pass rate
            print(f"{YELLOW}⚠ MINOR ISSUES DETECTED - SYSTEM MOSTLY OPERATIONAL{RESET}")
            return 1
        else:
            print(f"{RED}✗ CRITICAL ISSUES DETECTED - SYSTEM REQUIRES ATTENTION{RESET}")
            return 2

    async def run_all(self):
        """Run all verification tests"""
        self.print_header()

        try:
            await self.test_infrastructure()
            await self.test_platform_integrations()
            await self.test_webhooks()
            await self.test_unified_endpoints()
            await self.test_security()
            await self.test_performance()

        finally:
            await self.client.aclose()

        return self.print_summary()


async def main():
    """Main entry point"""
    base_url = os.getenv("SYSTEM_URL", "http://localhost")

    verifier = SystemVerification(base_url)
    exit_code = await verifier.run_all()

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())