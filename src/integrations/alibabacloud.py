import asyncio
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_accessanalyzer20200901 import models as accessanalyzer_models
from alibabacloud_accessanalyzer20200901.client import Client as AccessAnalyzerClient
from ..core.config import settings


class AlibabaCloudConfig(BaseModel):
    """Configuration for Alibaba Cloud integration"""
    access_key_id: str = Field(..., description="Alibaba Cloud Access Key ID")
    secret_key: str = Field(..., description="Alibaba Cloud Secret Key")
    region_id: str = Field(default="cn-hangzhou", description="Alibaba Cloud Region ID")


class AlibabacloudAPIError(Exception):
    """Custom exception for Alibaba Cloud API errors"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        """
        Initialize the AlibabacloudAPIError with a message and an optional original exception.
        
        Parameters:
            message (str): Human-readable description of the error.
            original_exception (Optional[Exception]): The underlying exception that caused this error, if available; stored on the `original_exception` attribute.
        """
        super().__init__(message)
        self.original_exception = original_exception


class AlibabaCloudIntegration:
    """
    Alibaba Cloud Integration Class with Security Hardening
    Provides integration with Alibaba Cloud services (Access Analyzer)
    """

    def __init__(self, config: AlibabaCloudConfig):
        """
        Initialize the integration with the provided AlibabaCloudConfig.
        
        Parameters:
            config (AlibabaCloudConfig): Configuration containing credentials and region used to create Alibaba Cloud clients and control integration behavior.
        """
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
        Retrieve security findings from Alibaba Cloud Access Analyzer.
        
        Aggregates findings from all available analyzers into a list of dictionaries. Each finding dictionary contains the keys: `id`, `resource`, `status`, `severity`, `principal`, `condition`, `created_at`, `analyzer_name`, and `analyzer_type`.
        
        Returns:
            List[Dict[str, Any]]: A list of finding dictionaries as described above.
        
        Raises:
            AlibabacloudAPIError: If the Alibaba Cloud API calls fail or an error occurs while fetching findings.
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
            self.logger.exception(f"Alibaba Cloud API error: {str(e)}")
            raise AlibabacloudAPIError(f"Failed to retrieve security findings: {str(e)}", original_exception=e)


# For backward compatibility
async def create_alibaba_cloud_integration() -> AlibabaCloudIntegration:
    """
    Create an AlibabaCloudIntegration configured from application settings.
    
    Constructs an AlibabaCloudConfig using ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_SECRET_KEY,
    and ALIBABA_CLOUD_REGION_ID from the global settings and returns an integration instance.
    
    Returns:
        AlibabaCloudIntegration: Integration initialized with credentials and region from settings.
    """
    config = AlibabaCloudConfig(
        access_key_id=settings.ALIBABA_CLOUD_ACCESS_KEY_ID,
        secret_key=settings.ALIBABA_CLOUD_SECRET_KEY,
        region_id=settings.ALIBABA_CLOUD_REGION_ID
    )
    return AlibabaCloudIntegration(config)