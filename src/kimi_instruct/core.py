import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from pathlib import Path

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    assigned_to: str  # "kimi" or "human"
    created_at: datetime
    due_date: Optional[datetime]
    metadata: Dict[str, Any]
    dependencies: List[str]
    human_approval_required: bool
    execution_callback: Optional[Callable] = None

@dataclass
class ProjectContext:
    current_phase: str
    objectives: List[str]
    constraints: List[str]
    metrics: Dict[str, float]
    last_human_checkin: datetime
    risk_level: str
    budget_remaining: float
    timeline_status: str

class KimiInstruct:
    """
    Hybrid AI Project Manager that orchestrates the LabVerse monitoring stack
    """

    def __init__(self, config_path: str = "config/kimi_instruct.json"):
        self.config = self.load_config(config_path)
        self.tasks: Dict[str, Task] = {}
        self.context = ProjectContext(
            current_phase="initialization",
            objectives=self.config.get("project_objectives", []),
            constraints=self.config.get("constraints", []),
            metrics={"progress": 0.0, "risk_score": 0.1, "human_intervention_count": 0},
            last_human_checkin=datetime.now(),
            risk_level="low",
            budget_remaining=50000.0,
            timeline_status="on_track"
        )
        self.decision_history = []
        self.human_oversight_mode = self.config.get("human_oversight_mode", "collaborative")
        self.setup_logging()

    def setup_logging(self):
        """Setup structured logging for Kimi Instruct"""
        self.logger = logging.getLogger("kimi_instruct")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load Kimi Instruct configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.create_default_config()

    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "human_oversight_mode": "collaborative",
            "auto_execution_threshold": 0.7,
            "human_checkin_interval_hours": 24,
            "max_concurrent_tasks": 5,
            "risk_thresholds": {"low": 0.3, "medium": 0.6, "high": 0.8},
            "escalation_rules": {
                "budget_exceeded": "immediate",
                "timeline_at_risk": "within_4_hours",
                "technical_blocker": "within_1_hour"
            },
            "project_objectives": ["Deploy production monitoring", "Achieve 99.9% uptime"],
            "constraints": ["Budget: $50K MRR target", "Timeline: 90 days"]
        }

    async def create_task(self,
                         title: str,
                         description: str,
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         assigned_to: str = "kimi",
                         due_date: Optional[datetime] = None,
                         dependencies: List[str] = None,
                         human_approval_required: bool = False,
                         execution_callback: Optional[Callable] = None,
                         metadata: Dict[str, Any] = None) -> Task:
        """Create a new task with Kimi oversight"""

        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(title) % 10000}"

        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            assigned_to=assigned_to,
            created_at=datetime.now(),
            due_date=due_date,
            dependencies=dependencies or [],
            human_approval_required=human_approval_required,
            execution_callback=execution_callback,
            metadata=metadata or {}
        )

        self.tasks[task_id] = task
        self.logger.info(f"Created task: {task_id} - {title}", extra={'task_id': task_id})

        if assigned_to == "kimi" and not human_approval_required:
            asyncio.create_task(self.execute_task(task_id))

        return task

    async def execute_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Task not found: {task_id}")
            return False

        task.status = TaskStatus.IN_PROGRESS
        self.logger.info(f"Executing task: {task_id}")

        try:
            # Placeholder for actual task execution
            await asyncio.sleep(1)
            task.status = TaskStatus.COMPLETED
            self.logger.info(f"Task completed: {task_id}")
            return True
        except Exception as e:
            task.status = TaskStatus.BLOCKED
            task.metadata['error'] = str(e)
            self.logger.error(f"Task execution failed: {task_id}", exc_info=True)
            await self.escalate_task(task, e)
            return False

    async def escalate_task(self, task: Task, error: Exception):
        self.logger.critical(f"Task escalation: {task.id}", extra={'error': str(error)})
        # In a real scenario, this would trigger notifications

    async def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""

        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)

        return {
            'timestamp': datetime.now().isoformat(),
            'project_context': asdict(self.context),
            'task_summary': {
                'total': total_tasks,
                'completed': completed_tasks,
                'completion_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            }
        }

__all__ = ['KimiInstruct', 'Task', 'TaskPriority', 'TaskStatus', 'ProjectContext']