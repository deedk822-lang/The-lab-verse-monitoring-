"""
Platform-specific connector implementations
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .manager import BasePlatformConnector

logger = logging.getLogger(__name__)


class GrafanaConnector(BasePlatformConnector):
    """Grafana integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="grafana",
            base_url=os.getenv("GRAFANA_URL", "https://somoleli.grafana.net"),
            api_key=os.getenv("GRAFANA_API_KEY"),
            redis_client=redis_client,
            cache_ttl=300  # 5 minutes
        )
        self.org_id = os.getenv("GRAFANA_ORG_ID")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards"""
        cache_key = "dashboards"

        # Try cache first
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Fetch from API
        data = await self._make_request("GET", "/api/search?type=dash-db")

        if data:
            await self._set_cache(cache_key, data)
            return data

        return []

    async def get_dashboard_stats(self, dashboard_uid: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific dashboard"""
        cache_key = f"dashboard_stats:{dashboard_uid}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", f"/api/dashboards/uid/{dashboard_uid}")

        if data:
            await self._set_cache(cache_key, data, ttl=600)  # 10 minutes
            return data

        return None

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all alert rules"""
        data = await self._make_request("GET", "/api/alerting/alerts")
        return data if data else []

    async def create_annotation(
        self,
        text: str,
        tags: List[str],
        time: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Create an annotation"""
        payload = {
            "text": text,
            "tags": tags,
            "time": time or int(datetime.utcnow().timestamp() * 1000)
        }

        return await self._make_request("POST", "/api/annotations", json=payload)

    async def sync(self) -> Dict[str, Any]:
        """Sync Grafana data"""
        dashboards = await self.get_dashboards()
        alerts = await self.get_alerts()

        return {
            "dashboards_count": len(dashboards),
            "alerts_count": len(alerts),
            "synced_at": datetime.utcnow().isoformat()
        }


class HuggingFaceConnector(BasePlatformConnector):
    """Hugging Face integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="huggingface",
            base_url="https://huggingface.co/api",
            api_key=os.getenv("HUGGINGFACE_TOKEN"),
            redis_client=redis_client,
            cache_ttl=900  # 15 minutes
        )
        self.username = os.getenv("HUGGINGFACE_USERNAME", "Papimashala")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_spaces(self) -> List[Dict[str, Any]]:
        """Get user's spaces"""
        cache_key = f"spaces:{self.username}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", f"/spaces/{self.username}")

        if data:
            await self._set_cache(cache_key, data)
            return data

        return []

    async def get_space_status(self, space_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific space"""
        full_name = f"{self.username}/{space_name}"
        data = await self._make_request("GET", f"/spaces/{full_name}/runtime")
        return data

    async def get_models(self) -> List[Dict[str, Any]]:
        """Get user's models"""
        cache_key = f"models:{self.username}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", f"/models?author={self.username}")

        if data:
            await self._set_cache(cache_key, data)
            return data

        return []

    async def sync(self) -> Dict[str, Any]:
        """Sync Hugging Face data"""
        spaces = await self.get_spaces()
        models = await self.get_models()

        # Get status for each space
        space_statuses = []
        space_limit = int(os.getenv("HUGGINGFACE_SPACE_SYNC_LIMIT", "5"))
        for space in spaces[:space_limit]:
            status = await self.get_space_status(space.get("id", ""))
            if status:
                space_statuses.append(status)

        return {
            "spaces_count": len(spaces),
            "models_count": len(models),
            "active_spaces": len([s for s in space_statuses if s.get("stage") == "RUNNING"]),
            "synced_at": datetime.utcnow().isoformat()
        }


class DataDogConnector(BasePlatformConnector):
    """DataDog integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="datadog",
            base_url=f"https://api.{os.getenv('DATADOG_SITE', 'datadoghq.eu')}",
            api_key=os.getenv("DATADOG_API_KEY"),
            redis_client=redis_client,
            cache_ttl=300  # 5 minutes
        )
        self.app_key = os.getenv("DATADOG_APP_KEY")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["DD-API-KEY"] = self.api_key
        headers["DD-APPLICATION-KEY"] = self.app_key
        return headers

    async def get_service_metrics(self, service: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a service"""
        cache_key = f"service_metrics:{service}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Query metrics for the last hour
        now = int(datetime.utcnow().timestamp())
        from_ts = now - 3600

        query = f"avg:system.cpu.user{{service:{service}}}"

        data = await self._make_request(
            "GET",
            f"/api/v1/query?query={query}&from={from_ts}&to={now}"
        )

        if data:
            await self._set_cache(cache_key, data)
            return data

        return None

    async def get_monitors(self) -> List[Dict[str, Any]]:
        """Get all monitors"""
        data = await self._make_request("GET", "/api/v1/monitor")
        return data if data else []

    async def get_ci_pipelines(self) -> Optional[Dict[str, Any]]:
        """Get CI pipeline metrics"""
        cache_key = "ci_pipelines"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", "/api/v2/ci/pipelines")

        if data:
            await self._set_cache(cache_key, data, ttl=600)
            return data

        return None

    async def sync(self) -> Dict[str, Any]:
        """Sync DataDog data"""
        monitors = await self.get_monitors()
        pipelines = await self.get_ci_pipelines()

        return {
            "monitors_count": len(monitors),
            "pipelines_data": pipelines is not None,
            "synced_at": datetime.utcnow().isoformat()
        }


class HubSpotConnector(BasePlatformConnector):
    """HubSpot integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="hubspot",
            base_url="https://api.hubapi.com",
            api_key=os.getenv("HUBSPOT_ACCESS_TOKEN"),
            redis_client=redis_client,
            cache_ttl=600  # 10 minutes
        )

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contacts"""
        cache_key = f"contacts:limit_{limit}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request(
            "GET",
            f"/crm/v3/objects/contacts?limit={limit}"
        )

        if data and "results" in data:
            await self._set_cache(cache_key, data["results"])
            return data["results"]

        return []

    async def get_deals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get deals"""
        cache_key = f"deals:limit_{limit}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request(
            "GET",
            f"/crm/v3/objects/deals?limit={limit}"
        )

        if data and "results" in data:
            await self._set_cache(cache_key, data["results"])
            return data["results"]

        return []

    async def create_contact(
        self,
        email: str,
        properties: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Create a new contact"""
        payload = {
            "properties": {
                "email": email,
                **properties
            }
        }

        return await self._make_request(
            "POST",
            "/crm/v3/objects/contacts",
            json=payload
        )

    async def sync(self) -> Dict[str, Any]:
        """Sync HubSpot data"""
        contacts = await self.get_contacts()
        deals = await self.get_deals()

        return {
            "contacts_count": len(contacts),
            "deals_count": len(deals),
            "synced_at": datetime.utcnow().isoformat()
        }


class ConfluenceConnector(BasePlatformConnector):
    """Atlassian Confluence integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="confluence",
            base_url=os.getenv("CONFLUENCE_URL", "https://lab-verse.atlassian.net") + "/wiki/rest/api",
            api_key=os.getenv("CONFLUENCE_API_TOKEN"),
            redis_client=redis_client,
            cache_ttl=3600  # 1 hour
        )
        self.username = os.getenv("CONFLUENCE_USERNAME", "dmakansomoleli@gmail.com")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        import base64
        auth_string = f"{self.username}:{self.api_key}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {auth_bytes}"
        return headers

    async def get_spaces(self) -> List[Dict[str, Any]]:
        """Get all spaces"""
        data = await self._make_request("GET", "/space?limit=100")
        return data.get("results", []) if data else []

    async def get_pages(self, space_key: str) -> List[Dict[str, Any]]:
        """Get pages in a space"""
        cache_key = f"pages:{space_key}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request(
            "GET",
            f"/content?spaceKey={space_key}&type=page&limit=100"
        )

        if data and "results" in data:
            await self._set_cache(cache_key, data["results"])
            return data["results"]

        return []

    async def get_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get content of a specific page"""
        data = await self._make_request(
            "GET",
            f"/content/{page_id}?expand=body.storage,version"
        )
        return data

    async def sync(self) -> Dict[str, Any]:
        """Sync Confluence data"""
        spaces = await self.get_spaces()

        # Get pages from first space
        total_pages = 0
        if spaces:
            pages = await self.get_pages(spaces[0].get("key", ""))
            total_pages = len(pages)

        return {
            "spaces_count": len(spaces),
            "pages_count": total_pages,
            "synced_at": datetime.utcnow().isoformat()
        }


class ClickUpConnector(BasePlatformConnector):
    """ClickUp integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="clickup",
            base_url="https://api.clickup.com/api/v2",
            api_key=os.getenv("CLICKUP_API_TOKEN"),
            redis_client=redis_client,
            cache_ttl=300  # 5 minutes
        )
        self.workspace_id = os.getenv("CLICKUP_WORKSPACE_ID")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["Authorization"] = self.api_key
        return headers

    async def get_spaces(self) -> List[Dict[str, Any]]:
        """Get all spaces in workspace"""
        data = await self._make_request("GET", f"/team/{self.workspace_id}/space")
        return data.get("spaces", []) if data else []

    async def get_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        """Get tasks in a list"""
        cache_key = f"tasks:{list_id}"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", f"/list/{list_id}/task")

        if data and "tasks" in data:
            await self._set_cache(cache_key, data["tasks"])
            return data["tasks"]

        return []

    async def create_task(
        self,
        list_id: str,
        name: str,
        description: str = "",
        priority: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Create a new task"""
        payload = {
            "name": name,
            "description": description,
            "priority": priority
        }

        return await self._make_request(
            "POST",
            f"/list/{list_id}/task",
            json=payload
        )

    async def sync(self) -> Dict[str, Any]:
        """Sync ClickUp data"""
        spaces = await self.get_spaces()

        return {
            "spaces_count": len(spaces),
            "synced_at": datetime.utcnow().isoformat()
        }


class CodeRabbitConnector(BasePlatformConnector):
    """CodeRabbit integration connector"""

    def __init__(self, redis_client):
        super().__init__(
            platform_name="coderabbit",
            base_url="https://api.coderabbit.ai",
            api_key=os.getenv("CODERABBIT_API_KEY"),
            redis_client=redis_client,
            cache_ttl=600  # 10 minutes
        )
        self.org = os.getenv("CODERABBIT_ORG", "deedk822-lang")

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_review_metrics(self) -> Optional[Dict[str, Any]]:
        """Get code review metrics"""
        cache_key = "review_metrics"

        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        data = await self._make_request("GET", f"/v1/orgs/{self.org}/metrics")

        if data:
            await self._set_cache(cache_key, data)
            return data

        return None

    async def get_quality_score(self) -> Optional[float]:
        """Get overall code quality score"""
        metrics = await self.get_review_metrics()
        return metrics.get("quality_score") if metrics else None

    async def sync(self) -> Dict[str, Any]:
        """Sync CodeRabbit data"""
        metrics = await self.get_review_metrics()
        quality_score = await self.get_quality_score()

        return {
            "has_metrics": metrics is not None,
            "quality_score": quality_score,
            "synced_at": datetime.utcnow().isoformat()
        }