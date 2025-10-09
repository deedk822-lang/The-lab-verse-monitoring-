"""
Kimi Instruct - Hybrid AI Project Manager

A comprehensive AI-powered project management system that combines
automated task execution with human oversight for the LabVerse
monitoring infrastructure.

Key Features:
- Autonomous task creation and execution
- Human approval workflows for critical decisions
- Project risk assessment and budget tracking
- Integration with monitoring stack (Prometheus, Grafana)
- Web dashboard and CLI interface
- Real-time status reporting and escalation
"""

__version__ = "1.0.0"
__author__ = "LabVerse Team"
__description__ = "Hybrid AI Project Manager for monitoring infrastructure"

from .core import (
    KimiInstruct,
    Task,
    TaskPriority,
    TaskStatus,
    ProjectContext
)

__all__ = [
    "KimiInstruct",
    "Task",
    "TaskPriority", 
    "TaskStatus",
    "ProjectContext"
]
