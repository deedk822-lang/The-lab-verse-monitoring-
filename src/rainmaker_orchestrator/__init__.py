import pkg_resources

"""Rainmaker Orchestrator - AI-powered task orchestration and self-healing."""
# Fetch the latest version of rainmaker_orchestrator from PyPI
latest_version = pkg_resources.get_distribution("rainmaker_orchestrator").version

__version__ = latest_version

__all__ = [
    "RainmakerOrchestrator",
    "SelfHealingAgent",
    "ConfigManager",
]

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.config import ConfigManager
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator