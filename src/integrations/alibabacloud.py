import asyncio
import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_accessanalyzer20200901 import models as accessanalyzer_models
from alibabacloud_accessanalyzer20200901.client import Client as AccessAnalyzerClient


class AlibabaCloudConfig(BaseModel):
    """Configuration for Alibaba Cloud integration"""
    access_key_id: str = Field(..., description="Alibaba Cloud Access Key ID")
    secret_key: str = Field(..., description="Alibaba Cloud Secret Key")
    region_id: str = Field(default="cn-hangzhou", description="Alibaba Cloud Region ID")


class AlibabaCloudIntegration:
    """
    Alibaba Cloud Integration Class with Security Hardening
    """

    def __init__(self, config: AlibabaCloudConfig):
        self.config = config
        self.access_analyzer_client = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        config = open_api_models.Config(
            access_key_id=self.config.access_key_id,
            access_key_secret=self.config.secret_key,
            region_id=self.config.region_id
        )
        # Initialize the synchronous client
        self.access_analyzer_client = AccessAnalyzerClient(config)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.access_analyzer_client = None

    async def get_security_findings(self) -> List[Dict[str, Any]]:
        """
        Get security findings from Alibaba Cloud Access Analyzer.
        Uses asyncio.to_thread to run the synchronous SDK in a non-blocking way.
        """
        try:
            # 1. List Analyzers (Synchronous call wrapped in thread)
            list_analyzers_request = accessanalyzer_models.ListAnalyzersRequest()
            # Use asyncio.to_thread to prevent blocking the event loop
            analyzers_response = await asyncio.to_thread(
                self.access_analyzer_client.list_analyzers,
                list_analyzers_request
            )

            all_findings = []

            if not analyzers_response.body.analyzers:
                self.logger.warning("No analyzers found in Alibaba Cloud.")
                return []

            # Process each analyzer
            for analyzer in analyzers_response.body.analyzers:
                # 2. List Findings (Synchronous call wrapped in thread)
                list_findings_request = accessanalyzer_models.ListFindingsRequest(
                    analyzer_name=analyzer.name
                )

                findings_response = await asyncio.to_thread(
                    self.access_analyzer_client.list_findings,
                    list_findings_request
                )

                if findings_response.body.findings:
                    for finding in findings_response.body.findings:
                        finding_dict = {
                            "id": finding.id,
                            "resource": finding.resource,
                            "status": finding.status,
                            "severity": finding.severity,
                            "principal": finding.principal if hasattr(finding, 'principal') else "N/A",
                            "condition": finding.condition if hasattr(finding, 'condition') else {},
                            "created_at": finding.created_at,
                            "analyzer_name": analyzer.name,
                            "analyzer_type": analyzer.type
                        }
                        all_findings.append(finding_dict)

            return all_findings

        except Exception as e:
            self.logger.error(f"Error getting security findings: {str(e)}")
            # Return empty list to avoid crashing the orchestrator on API failure
            return []


# For backward compatibility
async def create_alibaba_cloud_integration() -> AlibabaCloudIntegration:
    """Factory function to create Alibaba Cloud integration"""
    config = AlibabaCloudConfig(
        access_key_id="",
        secret_key="",
        region_id="cn-hangzhou"
    )
    return AlibabaCloudIntegration(config)
