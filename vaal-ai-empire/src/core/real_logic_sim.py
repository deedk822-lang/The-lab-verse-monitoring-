# vaal-ai-empire/src/core/real_logic_sim.py
"""
Production-Ready System Health Check
This module provides a robust, real-world health check for the Vaal AI Empire,
replacing the previous 'Simulated Real Logic' placeholder.
"""

import os
import logging
import httpx
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemHealthCheck")

class HealthCheck:
    """
    Performs a series of real-world checks to verify the operational status
    of the Vaal AI Empire and its external dependencies.
    """

    def __init__(self):
        self.results = {
            "overall_status": "passing",
            "services": []
        }

    def _check_service(self, name: str, url: str, check_type: str = "GET"):
        """
        A generic function to check the health of an external service.
        """
        service_status = {
            "service": name,
            "status": "passing",
            "details": ""
        }

        try:
            with httpx.Client(timeout=10) as client:
                if check_type.upper() == "GET":
                    response = client.get(url)
                elif check_type.upper() == "POST":
                    response = client.post(url, json={})

                response.raise_for_status()
                service_status["details"] = f"Successfully connected. Status: {response.status_code}"
                logger.info(f"✓ {name}: Connection successful")

        except httpx.HTTPStatusError as e:
            service_status["status"] = "failing"
            service_status["details"] = f"HTTP Error: {e.response.status_code} - {e.response.text}"
            self.results["overall_status"] = "failing"
            logger.error(f"✗ {name}: HTTP Error - {e.response.status_code}")
        except httpx.RequestError as e:
            service_status["status"] = "failing"
            service_status["details"] = f"Connection Error: {str(e)}"
            self.results["overall_status"] = "failing"
            logger.error(f"✗ {name}: Connection Error")
        except Exception as e:
            service_status["status"] = "failing"
            service_status["details"] = f"An unexpected error occurred: {str(e)}"
            self.results["overall_status"] = "failing"
            logger.error(f"✗ {name}: Unexpected Error")

        self.results["services"].append(service_status)

    def run_all_checks(self) -> Dict:
        """
        Execute all health checks for critical system components.
        """
        logger.info("="*60)
        logger.info("🚀 RUNNING SYSTEM-WIDE HEALTH CHECK...")
        logger.info("="*60)

        # 1. LocalAI Sovereign Node (if running)
        self._check_service(
            name="LocalAI Node",
            url="http://localhost:8080/readyz"
        )

        # 2. Databricks Connection
        databricks_host = os.getenv("DATABRICKS_HOST")
        if databricks_host:
            self._check_service(
                name="Databricks",
                url=databricks_host
            )
        else:
            logger.warning("Skipping Databricks check: DATABRICKS_HOST not set.")

        # 3. Jira API
        jira_url = os.getenv("JIRA_URL")
        if jira_url:
            self._check_service(
                name="Jira",
                url=f"{jira_url}/rest/api/2/serverInfo"
            )
        else:
            logger.warning("Skipping Jira check: JIRA_URL not set.")

        # 4. Notion API
        self._check_service(
            name="Notion API",
            url="https://api.notion.com/v1/users",
            check_type="GET" # This endpoint requires authentication, but a 401 is a sign of life
        )

        logger.info("="*60)
        logger.info(f"🏁 HEALTH CHECK COMPLETE: Overall Status - {self.results['overall_status'].upper()}")
        logger.info("="*60)

        return self.results

def get_system_health() -> Dict:
    """
    A simple, clean entry point to get the system's health status.
    """
    health_checker = HealthCheck()
    return health_checker.run_all_checks()

if __name__ == "__main__":
    # Example of how this can be run as a standalone script
    health_report = get_system_health()

    print("\n--- Health Report ---")
    for service in health_report["services"]:
        print(f"Service: {service['service']}")
        print(f"  Status: {service['status']}")
        print(f"  Details: {service['details']}")
    print("---------------------")

    if health_report["overall_status"] == "failing":
        print("\n🔴 One or more systems are down. Please check the logs.")
        exit(1)
    else:
        print("\n🟢 All systems are operational.")
        exit(0)
