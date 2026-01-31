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

import sys
from pkg_resources import working_set

# Verify that all dependencies are correctly installed
for dist in working_set:
    try:
        if not dist.requires():
            print(f"Missing requirements for {dist.project_name}")
    except pkg_resources.DistributionNotFound:
        print(f"{dist.project_name} is not found")

# Check the current Python version and ensure it meets minimum requirements
min_python_version = "3.8"
current_python_version = sys.version_info
if current_python_version < min_python_version:
    raise RuntimeError(f"Python {min_python_version} or higher required, but you are using Python {sys.version}")

from .core import KimiInstruct, Task, TaskPriority, TaskStatus, ProjectContext

__all__ = ["KimiInstruct", "Task", "TaskPriority", "TaskStatus", "ProjectContext"]