"""
Trust Boundary and Dry-Run Mode
Ensures security by preventing unauthorized execution during analysis
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional


class FixAction(Enum):
    """Types of actions the agent can take"""
    CREATE_PYTHON_FILE = "create_python_file"
    UPDATE_REQUIREMENTS = "update_requirements"
    REMOVE_SUBMODULE = "remove_submodule"
    MODIFY_FILE = "modify_file"


class FixIntent:
    """Represents an intended change to the codebase"""
    def __init__(self, action: FixAction, target_path: Path, content: str = ""):
        self.action = action
        self.target_path = target_path
        self.content = content


class DryRunMode:
    """
    Manages dry-run execution mode.
    In this mode, no changes are actually written to disk.
    """
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.fixes: List[FixIntent] = []

    def record_fix(self, intent: FixIntent):
        """Record a fix for later review without applying it"""
        self.fixes.append(intent)
        print(f"[DRY-RUN] Intended action: {intent.action.value} on {intent.target_path}")

    def get_summary(self) -> List[str]:
        """Get summary of all intended fixes"""
        return [f"{f.action.value}: {f.target_path}" for f in self.fixes]
