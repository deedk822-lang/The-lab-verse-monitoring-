"""
Kimi Instruct - Hybrid AI Project Manager
Manages the LabVerse monitoring stack with human oversight
"""
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
            objectives=["Deploy production monitoring", "Achieve 99.9% uptime", "Optimize costs by 70%"],
            constraints=["Budget: $50K MRR target", "Timeline: 90 days", "Region: Africa-focused"],
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
        except FileNotFoundError:
            return self.create_default_config()

    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "human_oversight_mode": "collaborative",
            "auto_execution_threshold": 0.7,  # Confidence threshold for auto-execution
            "human_checkin_interval_hours": 24,
            "max_concurrent_tasks": 5,
            "risk_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8
            },
            "escalation_rules": {
                "budget_exceeded": "immediate",
                "timeline_at_risk": "within_4_hours",
                "technical_blocker": "within_1_hour"
            }
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
        self.logger.info(f"Created task: {task_id} - {title}", extra={
            'task_id': task_id,
            'priority': priority.value,
            'assigned_to': assigned_to,
            'human_approval_required': human_approval_required
        })
        
        # Auto-schedule if assigned to Kimi and no human approval needed
        if assigned_to == "kimi" and not human_approval_required:
            asyncio.create_task(self.execute_task(task_id))
        
        return task
    
    async def execute_task(self, task_id: str) -> bool:
        """Execute a task with Kimi oversight"""
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Task not found: {task_id}")
            return False
        
        if task.status != TaskStatus.PENDING:
            self.logger.warning(f"Task {task_id} is not pending", extra={
                'task_id': task_id,
                'current_status': task.status.value
            })
            return False
        
        # Check dependencies
        if not await self.check_dependencies(task):
            task.status = TaskStatus.BLOCKED
            self.logger.info(f"Task {task_id} blocked by dependencies", extra={
                'task_id': task_id,
                'dependencies': task.dependencies
            })
            return False
        
        # Execute based on task type
        task.status = TaskStatus.IN_PROGRESS
        self.logger.info(f"Executing task: {task_id}", extra={
            'task_id': task_id,
            'title': task.title
        })
        
        try:
            if task.execution_callback:
                result = await task.execution_callback(task)
            else:
                result = await self.default_task_execution(task)
            
            task.status = TaskStatus.COMPLETED
            task.metadata['completion_time'] = datetime.now().isoformat()
            task.metadata['result'] = result
            
            self.logger.info(f"Task completed: {task_id}", extra={
                'task_id': task_id,
                'result': result
            })
            
            # Update project metrics
            await self.update_project_metrics(task, result)
            
            return True
            
        except Exception as e:
            task.status = TaskStatus.BLOCKED
            task.metadata['error'] = str(e)
            
            self.logger.error(f"Task execution failed: {task_id}", extra={
                'task_id': task_id,
                'error': str(e)
            })
            
            # Escalate if needed
            await self.escalate_task(task, e)
            
            return False
    
    async def default_task_execution(self, task: Task) -> Dict[str, Any]:
        """Default execution logic for common tasks"""
        
        # Route to appropriate handler based on task type
        if "deploy" in task.title.lower():
            return await self.handle_deployment_task(task)
        elif "optimize" in task.title.lower():
            return await self.handle_optimization_task(task)
        elif "monitor" in task.title.lower():
            return await self.handle_monitoring_task(task)
        elif "test" in task.title.lower():
            return await self.handle_testing_task(task)
        else:
            return await self.handle_generic_task(task)
    
    async def handle_deployment_task(self, task: Task) -> Dict[str, Any]:
        """Handle deployment-related tasks"""
        self.logger.info(f"Handling deployment task: {task.title}")
        
        # Parse deployment parameters
        deployment_params = task.metadata.get('deployment_params', {})
        service = deployment_params.get('service')
        environment = deployment_params.get('environment', 'staging')
        
        # Check if human approval is needed for production
        if environment == 'production' and self.human_oversight_mode != "auto":
            return await self.request_human_approval(task, "Production deployment requires approval")
        
        # Execute deployment
        deployment_result = await self.execute_deployment(service, environment, deployment_params)
        
        return {
            "service": service,
            "environment": environment,
            "status": "deployed",
            "deployment_id": deployment_result.get('deployment_id'),
            "url": deployment_result.get('url')
        }
    
    async def handle_optimization_task(self, task: Task) -> Dict[str, Any]:
        """Handle optimization tasks using cost intelligence"""
        self.logger.info(f"Handling optimization task: {task.title}")
        
        # Simulate cost optimization result
        result = {
            'total_potential_savings': 2500.0,
            'optimizations': ['reduce_prometheus_retention', 'optimize_grafana_queries'],
            'roi_projection': {'roi': 1.8}
        }
        
        # If high savings detected, get human approval
        if result.get('total_potential_savings', 0) > 1000:
            return await self.request_human_approval(
                task, 
                f"High savings detected (${result['total_potential_savings']:.2f}). "
                "Implementation requires approval."
            )
        
        return {
            "savings": result.get('total_potential_savings'),
            "optimizations": len(result.get('optimizations', [])),
            "roi": result.get('roi_projection', {}).get('roi', 0)
        }
    
    async def handle_monitoring_task(self, task: Task) -> Dict[str, Any]:
        """Handle monitoring and alerting tasks"""
        self.logger.info(f"Handling monitoring task: {task.title}")
        
        monitoring_params = task.metadata.get('monitoring_params', {})
        check_type = monitoring_params.get('type', 'health')
        
        if check_type == 'health':
            return await self.perform_health_check(monitoring_params)
        elif check_type == 'metrics':
            return await self.collect_metrics(monitoring_params)
        elif check_type == 'alert':
            return await self.handle_alert(monitoring_params)
        else:
            return {"status": "unknown_check_type", "check_type": check_type}
    
    async def perform_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # Check Prometheus
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://prometheus:9090/-/healthy") as response:
                    health_status["checks"]["prometheus"] = {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_time": response.headers.get('X-Response-Time', 'unknown')
                    }
        except Exception as e:
            health_status["checks"]["prometheus"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check Grafana
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://grafana:3000/api/health") as response:
                    health_status["checks"]["grafana"] = {
                        "status": "healthy" if response.status == 200 else "unhealthy"
                    }
        except Exception as e:
            health_status["checks"]["grafana"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        return health_status
    
    async def handle_testing_task(self, task: Task) -> Dict[str, Any]:
        """Handle testing tasks"""
        return {"status": "completed", "tests_passed": True}
    
    async def handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic tasks"""
        return {"status": "completed", "result": "Generic task executed"}
    
    async def execute_deployment(self, service: str, environment: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment (stub implementation)"""
        return {
            'deployment_id': f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'url': f"http://{service}.{environment}.local"
        }
    
    async def collect_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics (stub implementation)"""
        return {"status": "completed", "metrics_collected": 100}
    
    async def handle_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert (stub implementation)"""
        return {"status": "acknowledged", "alert_resolved": True}
    
    async def request_human_approval(self, task: Task, reason: str) -> Dict[str, Any]:
        """Request human approval for a task"""
        
        self.logger.warning(f"Human approval required for task: {task.id}", extra={
            'task_id': task.id,
            'reason': reason
        })
        
        # Create approval request
        approval_request = {
            'task_id': task.id,
            'task_title': task.title,
            'reason': reason,
            'requested_at': datetime.now().isoformat(),
            'approval_url': f"http://localhost:3000/approve/{task.id}",
            'denial_url': f"http://localhost:3000/deny/{task.id}"
        }
        
        # Store in task metadata
        task.metadata['approval_request'] = approval_request
        task.status = TaskStatus.BLOCKED
        
        # Send notification (would integrate with Slack/email in production)
        await self.send_approval_notification(approval_request)
        
        return {
            "status": "approval_required",
            "reason": reason,
            "approval_request": approval_request
        }
    
    async def send_approval_notification(self, approval_request: Dict[str, Any]):
        """Send approval notification to human"""
        self.logger.info(f"Sending approval notification for task: {approval_request['task_id']}")
        
        # In production, this would send Slack message, email, etc.
        notification = {
            "type": "approval_required",
            "task_id": approval_request['task_id'],
            "task_title": approval_request['task_title'],
            "reason": approval_request['reason'],
            "approval_url": approval_request['approval_url'],
            "timestamp": approval_request['requested_at']
        }
        
        # Store for human review
        self.context.metrics['human_intervention_count'] += 1
        self.decision_history.append({
            "type": "approval_request",
            "data": notification,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info("Approval notification sent", extra=notification)
    
    async def escalate_task(self, task: Task, error: Exception):
        """Escalate a failed task"""
        
        escalation = {
            'task_id': task.id,
            'task_title': task.title,
            'error': str(error),
            'error_type': type(error).__name__,
            'escalation_time': datetime.now().isoformat(),
            'escalation_level': self.determine_escalation_level(task, error)
        }
        
        self.logger.critical(f"Task escalation: {task.id}", extra=escalation)
        
        # Store escalation
        self.decision_history.append({
            "type": "escalation",
            "data": escalation,
            "timestamp": datetime.now().isoformat()
        })
    
    def determine_escalation_level(self, task: Task, error: Exception) -> str:
        """Determine escalation level based on task and error"""
        
        # Budget-related errors
        if "budget" in str(error).lower() or task.metadata.get('budget_impact', 0) > 1000:
            return 'immediate'
        
        # Timeline-critical errors
        if 'timeline' in str(error).lower() or task.priority == TaskPriority.CRITICAL:
            return 'high'
        
        # Technical blockers
        if 'technical' in str(error).lower() or 'blocker' in str(error).lower():
            return 'high'
        
        return 'standard'
    
    async def update_project_metrics(self, task: Task, result: Dict[str, Any]):
        """Update project metrics based on task completion"""
        
        # Progress tracking
        if task.priority == TaskPriority.CRITICAL:
            self.context.metrics['progress'] += 10.0
        elif task.priority == TaskPriority.HIGH:
            self.context.metrics['progress'] += 5.0
        else:
            self.context.metrics['progress'] += 2.0
        
        # Budget tracking
        if 'cost' in result:
            self.context.budget_remaining -= result['cost']
        
        # Risk assessment
        if 'risk_score' in result:
            self.context.metrics['risk_score'] = result['risk_score']
            self.assess_project_risk()
        
        self.logger.info("Project metrics updated", extra={
            'progress': self.context.metrics['progress'],
            'budget_remaining': self.context.budget_remaining,
            'risk_score': self.context.metrics['risk_score']
        })
    
    def assess_project_risk(self):
        """Assess overall project risk"""
        risk_score = self.context.metrics['risk_score']
        
        if risk_score > self.config['risk_thresholds']['high']:
            self.context.risk_level = "high"
            self.logger.warning("Project risk level: HIGH", extra={
                'risk_score': risk_score,
                'threshold': self.config['risk_thresholds']['high']
            })
        elif risk_score > self.config['risk_thresholds']['medium']:
            self.context.risk_level = "medium"
            self.logger.info("Project risk level: MEDIUM", extra={
                'risk_score': risk_score,
                'threshold': self.config['risk_thresholds']['medium']
            })
        else:
            self.context.risk_level = "low"
            self.logger.debug("Project risk level: LOW", extra={
                'risk_score': risk_score
            })
    
    async def check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)
        
        # Calculate completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Identify critical issues
        critical_issues = []
        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED and task.priority == TaskPriority.CRITICAL:
                critical_issues.append({
                    'task_id': task.id,
                    'title': task.title,
                    'reason': task.metadata.get('error', 'Unknown blocker')
                })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'project_context': asdict(self.context),
            'task_summary': {
                'total': total_tasks,
                'completed': completed_tasks,
                'in_progress': in_progress_tasks,
                'blocked': blocked_tasks,
                'completion_percentage': completion_percentage
            },
            'critical_issues': critical_issues,
            'risk_level': self.context.risk_level,
            'next_actions': await self.get_next_actions(),
            'human_checkin_due': self.is_human_checkin_due(),
            'decision_history': self.decision_history[-10:]  # Last 10 decisions
        }
    
    async def get_next_actions(self) -> List[Dict[str, Any]]:
        """Get recommended next actions"""
        
        next_actions = []
        
        # Check for blocked critical tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED and task.priority == TaskPriority.CRITICAL:
                next_actions.append({
                    'priority': 'critical',
                    'action': 'resolve_blocker',
                    'task_id': task.id,
                    'task_title': task.title,
                    'description': f'Resolve blocker for critical task: {task.title}'
                })
        
        # Check for human checkin
        if self.is_human_checkin_due():
            next_actions.append({
                'priority': 'high',
                'action': 'human_checkin',
                'description': 'Daily human checkin due - review project status'
            })
        
        # Check budget
        if self.context.budget_remaining < 10000:  # Less than $10K remaining
            next_actions.append({
                'priority': 'high',
                'action': 'budget_review',
                'description': f'Budget review needed - ${self.context.budget_remaining:.2f} remaining'
            })
        
        # Check timeline
        if self.context.timeline_status == "at_risk":
            next_actions.append({
                'priority': 'high',
                'action': 'timeline_review',
                'description': 'Timeline review needed - project at risk'
            })
        
        return next_actions
    
    def is_human_checkin_due(self) -> bool:
        """Check if human checkin is due"""
        
        time_since_checkin = datetime.now() - self.context.last_human_checkin
        checkin_interval = timedelta(hours=self.config['human_checkin_interval_hours'])
        
        return time_since_checkin > checkin_interval

# Export for use in other modules
__all__ = ['KimiInstruct', 'Task', 'TaskPriority', 'TaskStatus', 'ProjectContext']