"""Rainmaker Orchestrator - AI-powered task orchestration and self-healing."""

__version__ = "0.1.0"

__all__ = [
    "RainmakerOrchestrator",
    "SelfHealingAgent",
    "ConfigManager",
]

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
try:
    from rainmaker_orchestrator.agents.healer import SelfHealingAgent
except ImportError:
    # Healer might be missing or moved
    SelfHealingAgent = None
from rainmaker_orchestrator.config import ConfigManager
