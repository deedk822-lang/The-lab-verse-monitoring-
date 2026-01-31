"""
Rainmaker Orchestrator - AI-powered task orchestration and self-healing.
"""

__version__ = "0.1.0"

__all__ = [
    "RainmakerOrchestrator",
    "SelfHealingAgent",
    "ConfigManager",
]

def main():
    """
    Main function to start the Rainmaker Orchestrator.
    """
    # Initialize and start the RainmakerOrchestrator
    orchestrator = RainmakerOrchestrator()
    orchestrator.start()

if __name__ == "__main__":
    main()