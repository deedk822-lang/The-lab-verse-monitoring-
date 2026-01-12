 feature/elite-ci-cd-pipeline-1070897568806221897
# This file makes this a Python package

"""Rainmaker Orchestrator - AI-powered task orchestration and self-healing."""

__version__ = "0.1.0"

__all__ = [
    "RainmakerOrchestrator",
    "SelfHealingAgent",
    "ConfigManager",
]

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.config import ConfigManager
 main
