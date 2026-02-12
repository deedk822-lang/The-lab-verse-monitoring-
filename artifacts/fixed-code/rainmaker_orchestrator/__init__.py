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

def main():
    # Initialize and run the Orchestrator
    orchestrator = RainmakerOrchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()