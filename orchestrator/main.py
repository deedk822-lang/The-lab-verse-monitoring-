"""
orchestrator/main.py - Autonomous Builder Platform Orchestrator
Version: 2.0.0 Production

Integrates LangChain agents with Moonshot Kimi for autonomous code generation.
No mock-ups - production-ready implementation.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.jules/logs/orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import our components
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.builder_agents import BuilderAgentSystem
from tools.confidence_scorer import ConfidenceScorer
from tools.validator import SecurityValidator
from tools.audit_logger import AuditLogger

# Prometheus metrics
TASKS_TOTAL = Counter('tasks_total', 'Total number of tasks submitted')
TASKS_SUCCESS = Counter('tasks_success', 'Successfully completed tasks')
TASKS_FAILED = Counter('tasks_failed', 'Failed tasks')
TASK_DURATION = Histogram('task_duration_seconds', 'Task execution duration')
CONFIDENCE_SCORE = Gauge('task_confidence_score', 'Latest task confidence score')
ACTIVE_TASKS = Gauge('active_tasks', 'Number of currently active tasks')

# FastAPI application
app = FastAPI(
    title="Autonomous Builder Platform",
    version="2.0.0",
    description="Hybrid Brain-to-Hands Autonomous Code Generation"
)

# Request models
class TaskRequest(BaseModel):
    intent: str
    type: str = "coding_task"
    scope: str = "targeted"
    auto_deploy: bool = True
    requester: str = "system"
    metadata: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    confidence: Optional[float] = None
    files_changed: Optional[int] = None
    pr_url: Optional[str] = None

# Global orchestrator instance
orchestrator = None


class AutonomousOrchestrator:
    """
    Main orchestrator that coordinates the Brain (LangChain + Kimi)
    and Hands (file system operations) for autonomous code generation.
    """

    def __init__(self):
        self.repo_root = Path(os.getenv('REPO_ROOT', os.getcwd()))
        self.auto_deploy_enabled = os.getenv('AUTO_DEPLOY_ENABLED', 'true').lower() == 'true'
        self.auto_merge_threshold = int(os.getenv('AUTO_MERGE_THRESHOLD', '95'))
        self.max_files_auto_merge = int(os.getenv('MAX_FILES_AUTO_MERGE', '10'))

        # Initialize components
        logger.info("Initializing Autonomous Orchestrator...")

        self.agent_system = BuilderAgentSystem()
        self.confidence_scorer = ConfidenceScorer()
        self.security_validator = SecurityValidator()
        self.audit_logger = AuditLogger()

        self.active_tasks: Dict[str, Dict] = {}

        logger.info("✓ Orchestrator initialized successfully")
        logger.info(f"  • Repository: {self.repo_root}")
        logger.info(f"  • Auto-deploy: {self.auto_deploy_enabled}")
        logger.info(f"  • Auto-merge threshold: {self.auto_merge_threshold}")

    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        import time
        import random
        timestamp = int(time.time())
        random_suffix = ''.join(str(random.randint(0, 9)) for _ in range(6))
        return f"task_{timestamp}_{random_suffix}"

    async def execute_task(self, request: TaskRequest) -> TaskResponse:
        """
        Execute a task through the complete pipeline:
        1. Plan with LangChain Planner Agent
        2. Validate with Validator Agent
        3. Generate code with Generator Agent
        4. Run security checks
        5. Calculate confidence
        6. Deploy based on confidence and settings
        """
        task_id = self.generate_task_id()
        start_time = datetime.now()

        # Update metrics
        TASKS_TOTAL.inc()
        ACTIVE_TASKS.inc()

        context = {
            'task_id': task_id,
            'intent': request.intent,
            'type': request.type,
            'scope': request.scope,
            'requester': request.requester,
            'timestamp': start_time.isoformat(),
            'metadata': request.metadata or {}
        }

        self.active_tasks[task_id] = context

        try:
            logger.info(f"[{task_id}] Starting task execution")
            logger.info(f"[{task_id}] Intent: {request.intent}")

            # Log task start
            await self.audit_logger.log_task_start(context)

            # Step 1: Plan with Planner Agent
            logger.info(f"[{task_id}] Step 1: Creating execution plan...")
            plan = await self.agent_system.create_plan(request.intent, context)

            if not plan or 'error' in plan:
                raise Exception(f"Planning failed: {plan.get('error', 'Unknown error')}")

            logger.info(f"[{task_id}] ✓ Plan created: {plan.get('summary', 'N/A')}")

            # Step 2: Initial validation
            logger.info(f"[{task_id}] Step 2: Validating plan...")
            validation_result = await self.agent_system.validate_plan(plan)

            if not validation_result['approved']:
                logger.warning(f"[{task_id}] Plan rejected: {validation_result['reason']}")
                return TaskResponse(
                    task_id=task_id,
                    status='rejected',
                    message=f"Plan rejected: {validation_result['reason']}"
                )

            logger.info(f"[{task_id}] ✓ Plan validated")

            # Step 3: Generate code
            logger.info(f"[{task_id}] Step 3: Generating code...")
            code_changes = await self.agent_system.generate_code(plan, context)

            if not code_changes or 'error' in code_changes:
                raise Exception(f"Code generation failed: {code_changes.get('error', 'Unknown error')}")

            files_count = len(code_changes.get('files', {}))
            logger.info(f"[{task_id}] ✓ Generated changes for {files_count} files")

            # Step 4: Security validation
            logger.info(f"[{task_id}] Step 4: Running security checks...")
            security_result = await self.security_validator.validate(code_changes)

            if security_result['critical_issues']:
                logger.error(f"[{task_id}] Critical security issues found")
                await self.audit_logger.log_security_rejection(task_id, security_result)
                return TaskResponse(
                    task_id=task_id,
                    status='security_rejected',
                    message=f"Critical security issues: {len(security_result['critical_issues'])} found"
                )

            logger.info(f"[{task_id}] ✓ Security validation passed")

            # Step 5: Calculate confidence
            logger.info(f"[{task_id}] Step 5: Calculating confidence score...")
            confidence = await self.confidence_scorer.calculate(
                code_changes=code_changes,
                security_result=security_result,
                plan=plan
            )

            confidence_score = confidence['score']
            CONFIDENCE_SCORE.set(confidence_score)

            logger.info(f"[{task_id}] ✓ Confidence score: {confidence_score}/100")

            # Step 6: Make deployment decision
            logger.info(f"[{task_id}] Step 6: Making deployment decision...")
            decision = self._make_deployment_decision(
                confidence_score=confidence_score,
                files_count=files_count,
                security_result=security_result,
                auto_deploy=request.auto_deploy
            )

            logger.info(f"[{task_id}] Decision: {decision['action']}")

            # Step 7: Execute deployment decision
            logger.info(f"[{task_id}] Step 7: Executing deployment...")
            deployment_result = await self._execute_deployment(
                task_id=task_id,
                decision=decision,
                code_changes=code_changes,
                confidence=confidence
            )

            # Update metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            TASK_DURATION.observe(elapsed)
            TASKS_SUCCESS.inc()
            ACTIVE_TASKS.dec()

            # Log completion
            await self.audit_logger.log_task_complete({
                **context,
                'outcome': deployment_result,
                'confidence': confidence_score,
                'files_changed': files_count,
                'duration_seconds': elapsed
            })

            logger.info(f"[{task_id}] ✓ Task completed successfully in {elapsed:.2f}s")

            return TaskResponse(
                task_id=task_id,
                status=deployment_result['status'],
                message=deployment_result['message'],
                confidence=confidence_score,
                files_changed=files_count,
                pr_url=deployment_result.get('pr_url')
            )

        except Exception as e:
            # Update metrics
            TASKS_FAILED.inc()
            ACTIVE_TASKS.dec()

            logger.error(f"[{task_id}] Task failed: {str(e)}", exc_info=True)

            # Log error
            await self.audit_logger.log_task_error(context, e)

            return TaskResponse(
                task_id=task_id,
                status='failed',
                message=f"Task execution failed: {str(e)}"
            )

        finally:
            self.active_tasks.pop(task_id, None)

    def _make_deployment_decision(
        self,
        confidence_score: float,
        files_count: int,
        security_result: Dict,
        auto_deploy: bool
    ) -> Dict[str, str]:
        """
        Decide deployment action based on confidence, security, and settings.

        Decision matrix:
        - confidence >= 95 + files <= 10 + auto_deploy = auto_merge
        - confidence >= 85 = create_pr
        - confidence >= 70 = draft_pr
        - confidence < 70 = notify_only
        """
        if not auto_deploy or not self.auto_deploy_enabled:
            return {'action': 'notify_only', 'reason': 'auto_deploy_disabled'}

        if security_result.get('high_issues', []):
            return {'action': 'create_pr', 'reason': 'security_review_required'}

        if confidence_score >= self.auto_merge_threshold and files_count <= self.max_files_auto_merge:
            return {'action': 'auto_merge', 'reason': 'high_confidence'}

        if confidence_score >= 85:
            return {'action': 'create_pr', 'reason': 'good_confidence'}

        if confidence_score >= 70:
            return {'action': 'draft_pr', 'reason': 'moderate_confidence'}

        return {'action': 'notify_only', 'reason': 'low_confidence'}

    async def _execute_deployment(
        self,
        task_id: str,
        decision: Dict,
        code_changes: Dict,
        confidence: Dict
    ) -> Dict[str, Any]:
        """Execute the deployment based on decision"""

        action = decision['action']

        if action == 'auto_merge':
            result = await self.agent_system.apply_and_merge(task_id, code_changes)
            return {
                'status': 'auto_merged',
                'message': 'Changes automatically merged to main branch',
                'pr_url': result.get('merge_url')
            }

        elif action == 'create_pr':
            result = await self.agent_system.create_pull_request(
                task_id=task_id,
                code_changes=code_changes,
                confidence=confidence,
                draft=False
            )
            return {
                'status': 'pr_created',
                'message': 'Pull request created for review',
                'pr_url': result.get('pr_url')
            }

        elif action == 'draft_pr':
            result = await self.agent_system.create_pull_request(
                task_id=task_id,
                code_changes=code_changes,
                confidence=confidence,
                draft=True
            )
            return {
                'status': 'draft_pr_created',
                'message': 'Draft pull request created',
                'pr_url': result.get('pr_url')
            }

        else:  # notify_only
            await self.agent_system.notify_review_needed(task_id, code_changes, confidence)
            return {
                'status': 'review_required',
                'message': f'Review required: {decision["reason"]}'
            }


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator
    logger.info("🚀 Starting Autonomous Builder Platform...")
    orchestrator = AutonomousOrchestrator()
    logger.info("✓ System ready for tasks")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Autonomous Builder Platform",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "tasks": "/tasks",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(orchestrator.active_tasks) if orchestrator else 0
    }


@app.post("/tasks", response_model=TaskResponse)
async def submit_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Submit a new task for autonomous execution.

    Example:
    ```
    {
        "intent": "Create a function to calculate fibonacci numbers",
        "type": "coding_task",
        "scope": "targeted",
        "auto_deploy": true
    }
    ```
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        response = await orchestrator.execute_task(request)
        return response
    except Exception as e:
        logger.error(f"Task submission failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    task = orchestrator.active_tasks.get(task_id)
    if not task:
        # Try to get from audit log
        task = await orchestrator.audit_logger.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.get("/agents/status")
async def agents_status():
    """Get status of all agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "planner": "active",
        "generator": "active",
        "validator": "active",
        "file_system": "active",
        "total_tasks_processed": TASKS_TOTAL._value.get()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv('ORCHESTRATOR_PORT', '8080'))

    logger.info(f"Starting server on port {port}...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )