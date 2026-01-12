#!/usr/bin/env python3
"""
Kimi Instruct Service - Production Implementation
Real AI-powered project manager with multi-provider support
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
from pathlib import Path
import uuid
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    print("Warning: prometheus_client not installed, metrics disabled")
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    
    def generate_latest(): return "# Prometheus not available"

try:
    from aiohttp_cors import setup as cors_setup, ResourceOptions
    CORS_AVAILABLE = True
except ImportError:
    print("Warning: aiohttp-cors not installed, CORS disabled")
    CORS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/kimi_instruct.log') if Path('logs').exists() else logging.NullHandler()
    ]
)
# Prometheus metrics
REQUEST_COUNT = Counter('kimi_requests_total', 'Total requests to Kimi API', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('kimi_request_duration_seconds', 'Request duration in seconds')
TASK_COUNT = Counter('kimi_tasks_total', 'Total tasks created', ['priority', 'status'])

def default_serializer(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

async def handle_status(request):
    """
    Handles requests for the Kimi Instruct status report.
    """
    kimi = request.app['kimi']
    report = await kimi.get_status_report()
    return web.json_response(report, dumps=lambda x: json.dumps(x, default=default_serializer))

async def handle_create_task(request):
    """
    Handles requests to create a new task.
    """
    try:
        kimi = request.app['kimi']
        data = await request.json()

        task = await kimi.create_task(
            title=data['title'],
            description=data.get('description', ''),
            priority=TaskPriority(data.get('priority', 'medium')),
            assigned_to=data.get('assigned_to', 'kimi'),
            human_approval_required=data.get('human_approval_required', False)
        )
        return web.json_response({'task_id': task.id}, status=201)
    except (KeyError, ValueError) as e:
        return web.json_response({'error': str(e)}, status=400)

async def handle_health(request):
    """
    A simple health check endpoint.
    """
    return web.json_response({"status": "healthy"})


logger = logging.getLogger('kimi_instruct')

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"
    CANCELLED = "cancelled"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(Enum):
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    BACKUP = "backup"
    MAINTENANCE = "maintenance"
    REVENUE_OPTIMIZATION = "revenue_optimization"
    A2A_NEGOTIATION = "a2a_negotiation"

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: Priority
    task_type: TaskType = TaskType.ANALYSIS
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    assigned_to: str = "kimi"
    requires_approval: bool = False
    progress: float = 0.0
    estimated_duration: int = 300  # seconds
    actual_duration: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    approval_reason: Optional[str] = None

    def to_dict(self):
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status.value,
            'priority': self.priority.value,
            'task_type': self.task_type.value
        }

@dataclass
class ProjectMetrics:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    progress_percentage: float = 0.0
    budget_used: float = 0.0
    budget_total: float = float(os.getenv("PROJECT_BUDGET", 100000))
    days_remaining: int = 30
    risk_score: float = 0.2
    efficiency_score: float = 0.8
    last_updated: datetime = field(default_factory=datetime.now)
    active_deployments: int = 0
    system_health: str = "healthy"
    mrr_projection: float = 0.0
    revenue_pipeline_health: float = 0.8

class AIEngine:
    """Production AI Engine with real provider integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self.session = None
        self.provider_config = self._load_provider_config()
        
        # Initialize providers based on available API keys
        self._initialize_providers()
        logger.info(f"AI Engine initialized with providers: {list(self.providers.keys())}")
    
    def _load_provider_config(self) -> Dict[str, Any]:
        """Load AI provider configuration from YAML file"""
        config_path = Path("config/ai_providers.yaml")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load AI provider config: {e}")
        return {}

    def _initialize_providers(self):
        """Initialize available AI providers"""
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-3.5-turbo"
            }
            logger.info("OpenAI provider initialized")
            
        # DashScope (Qwen)
        if os.getenv("DASHSCOPE_API_KEY"):
            self.providers["dashscope"] = {
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                "model": "qwen-turbo"
            }
            logger.info("DashScope (Qwen) provider initialized")
            
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers["anthropic"] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-sonnet-20240229"
            }
            logger.info("Anthropic provider initialized")
            
        # Moonshot AI
        if os.getenv("MOONSHOT_API_KEY"):
            self.providers["moonshot"] = {
                "api_key": os.getenv("MOONSHOT_API_KEY"),
                "base_url": "https://api.moonshot.cn/v1/chat/completions",
                "model": "moonshot-v1-8k"
            }
            logger.info("Moonshot AI provider initialized")

        # OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            self.providers["openrouter"] = {
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1/chat/completions",
            }
            logger.info("OpenRouter provider initialized")
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = ClientTimeout(total=30)
            self.session = ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def analyze_task(self, task: Task) -> Dict[str, Any]:
        """AI-powered task analysis with sophisticated routing"""
        if not self.providers:
            logger.warning("No AI providers available, using heuristic analysis")
            return self._heuristic_analysis(task)
        
        prompt = f"""
Analyze this project management task and provide comprehensive insights:

Task Details:
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority.value}
- Type: {task.task_type.value}
- Dependencies: {task.dependencies}

Provide analysis in JSON format:
{{
    "complexity_score": 0.1,
    "risk_assessment": "low",
    "estimated_effort_hours": 2,
    "required_skills": ["general"],
    "dependencies": [],
    "recommendations": ["Monitor progress"],
    "automation_potential": 0.7,
    "revenue_impact": 0.2,
    "ethical_considerations": ["Standard review"]
}}
"""
        
        try:
            # OpenRouter routing logic
            if "openrouter" in self.providers and self.provider_config.get("openrouter"):
                openrouter_conf = self.provider_config["openrouter"]

                # Try primary
                try:
                    model = openrouter_conf.get("primary")
                    logger.info(f"Attempting OpenRouter primary: {model}")
                    response = await self._call_openrouter(model, prompt)
                    return self._parse_ai_response(response)
                except Exception as e:
                    logger.warning(f"OpenRouter primary failed: {e}")

                # Try fallbacks
                for model in openrouter_conf.get("fallbacks", []):
                    try:
                        logger.info(f"Attempting OpenRouter fallback: {model}")
                        response = await self._call_openrouter(model, prompt)
                        return self._parse_ai_response(response)
                    except Exception as e:
                        logger.warning(f"OpenRouter fallback {model} failed: {e}")
                        continue

            # Direct provider routing as a final fallback
            direct_providers = self.provider_config.get("direct_providers", ["dashscope", "openai"])
            for provider_name in direct_providers:
                if provider_name in self.providers:
                    try:
                        response = await self._call_provider(provider_name, prompt)
                        return self._parse_ai_response(response)
                    except Exception as e:
                        logger.warning(f"Direct provider {provider_name} failed: {e}")
                        continue
            
            # If all providers fail, use heuristic
            logger.error("All AI providers failed, using heuristic analysis")
            return self._heuristic_analysis(task)
            
        except Exception as e:
            logger.error(f"AI analysis failed entirely: {e}")
            return self._heuristic_analysis(task)

    async def _call_provider(self, provider_name: str, prompt: str, model: Optional[str] = None) -> str:
        """Call specific AI provider"""
        provider = self.providers[provider_name]
        session = await self.get_session()
        
        if provider_name == "openai":
            return await self._call_openai(session, provider, prompt)
        elif provider_name == "dashscope":
            return await self._call_dashscope(session, provider, prompt)
        elif provider_name == "anthropic":
            return await self._call_anthropic(session, provider, prompt)
        elif provider_name == "moonshot":
            return await self._call_moonshot(session, provider, prompt)
        elif provider_name == "openrouter":
            return await self._call_openrouter(model, prompt)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    async def _call_openai(self, session: ClientSession, provider: Dict[str, str], prompt: str) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with session.post(provider["base_url"], headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"OpenAI API error: {response.status} - {error_text}")

    async def _call_dashscope(self, session: ClientSession, provider: Dict[str, str], prompt: str) -> str:
        """Call Alibaba DashScope API (Qwen model)"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider["model"],
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"result_format": "message", "temperature": 0.7}
        }
        
        async with session.post(provider["base_url"], headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result["output"]["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"DashScope API error: {response.status} - {error_text}")

    async def _call_anthropic(self, session: ClientSession, provider: Dict[str, str], prompt: str) -> str:
        """Call Anthropic API"""
        headers = {
            "x-api-key": provider["api_key"],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": provider["model"],
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with session.post(provider["base_url"], headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result["content"][0]["text"]
            else:
                error_text = await response.text()
                raise Exception(f"Anthropic API error: {response.status} - {error_text}")

    async def _call_moonshot(self, session: ClientSession, provider: Dict[str, str], prompt: str) -> str:
        """Call Moonshot AI API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        async with session.post(provider["base_url"], headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"Moonshot API error: {response.status} - {error_text}")

    async def _call_openrouter(self, model: str, prompt: str) -> str:
        """Call OpenRouter API"""
        provider = self.providers["openrouter"]
        session = await self.get_session()

        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with session.post(provider["base_url"], headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"OpenRouter API error: {response.status} - {error_text}")

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response with fallback handling"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback to heuristic parsing
            logger.warning("Failed to parse AI response as JSON, using heuristic")
            return {
                "complexity_score": 0.5,
                "risk_assessment": "medium",
                "estimated_effort_hours": 2,
                "required_skills": ["general"],
                "dependencies": [],
                "recommendations": ["AI analysis unavailable, manual review recommended"],
                "automation_potential": 0.3,
                "revenue_impact": 0.2,
                "ethical_considerations": ["Standard review required"]
            }

    def _heuristic_analysis(self, task: Task) -> Dict[str, Any]:
        """Fallback heuristic analysis when AI is unavailable"""
        complexity_indicators = ["production", "database", "security", "critical", "deployment", "revenue"]
        complexity_score = 0.3
        
        text = f"{task.title} {task.description}".lower()
        for indicator in complexity_indicators:
            if indicator in text:
                complexity_score += 0.15
        
        # Revenue impact analysis
        revenue_keywords = ["revenue", "monetization", "payment", "subscription", "mrr", "conversion"]
        revenue_impact = 0.1
        for keyword in revenue_keywords:
            if keyword in text:
                revenue_impact += 0.2
        
        risk_level = "critical" if complexity_score > 0.8 else "high" if complexity_score > 0.6 else "medium" if complexity_score > 0.4 else "low"
        
        return {
            "complexity_score": min(complexity_score, 1.0),
            "risk_assessment": risk_level,
            "estimated_effort_hours": complexity_score * 8,
            "required_skills": ["general", "devops"] if complexity_score > 0.5 else ["general"],
            "dependencies": [],
            "recommendations": [
                "Monitor progress closely",
                "Consider peer review" if complexity_score > 0.6 else "Standard execution",
                "Revenue impact assessment" if revenue_impact > 0.3 else "Low revenue impact"
            ],
            "automation_potential": max(0.0, 1.0 - complexity_score),
            "revenue_impact": min(revenue_impact, 1.0),
            "ethical_considerations": ["Standard compliance check"]
        }

class KimiService:
    """Web service for Kimi Instruct"""

    def __init__(self):
        self.kimi = KimiInstruct()
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()

    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/health', self.health)
        self.app.router.add_get('/metrics', self.metrics)

        # Status and reporting
        self.app.router.add_get('/status', self.get_status)
        self.app.router.add_get('/tasks', self.list_tasks)
        self.app.router.add_get('/tasks/{task_id}', self.get_task)

        # Task management
        self.app.router.add_post('/tasks', self.create_task)
        self.app.router.add_post('/tasks/{task_id}/execute', self.execute_task)
        self.app.router.add_post('/tasks/{task_id}/approve', self.approve_task)
        self.app.router.add_post('/tasks/{task_id}/deny', self.deny_task)

        # Human interaction
        self.app.router.add_post('/checkin', self.human_checkin)
        self.app.router.add_get('/next-actions', self.get_next_actions)

        # Dashboard
        self.app.router.add_get('/dashboard', self.dashboard)

        # Static files for dashboard
        self.app.router.add_static('/', path='static', name='static')

    def setup_cors(self):
        """Setup CORS for web dashboard"""
        import aiohttp_cors
        cors = cors_setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # Configure CORS for all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def index(self, request):
        """Main index page"""
        return web.json_response({
            "service": "Kimi Instruct",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                "/health", "/metrics", "/status", "/tasks", "/dashboard"
            ]
        })

    async def health(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })

    async def metrics(self, request):
        """Prometheus metrics endpoint"""
        # Update task metrics
        for task in self.kimi.tasks.values():
            TASK_COUNT.labels(
                priority=task.priority.value,
                status=task.status.value
            ).inc(0)  # Just to ensure labels exist

        return web.Response(
            text=generate_latest().decode('utf-8'),
            content_type=CONTENT_TYPE_LATEST
        )

    async def get_status(self, request):
        """Get project status"""
        with REQUEST_DURATION.time():
            try:
                status = await self.kimi.get_status_report()
                REQUEST_COUNT.labels(method='GET', endpoint='/status', status='200').inc()
                return web.json_response(status, dumps=lambda x: json.dumps(x, default=default_serializer))
            except Exception as e:
                REQUEST_COUNT.labels(method='GET', endpoint='/status', status='500').inc()
                return web.json_response(
                    {"error": str(e)},
                    status=500
                )

    async def list_tasks(self, request):
        """List all tasks"""
        try:
            tasks = []
            for task in self.kimi.tasks.values():
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "assigned_to": task.assigned_to,
                    "created_at": task.created_at.isoformat(),
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "human_approval_required": task.human_approval_required,
                    "metadata": task.metadata
                })

            REQUEST_COUNT.labels(method='GET', endpoint='/tasks', status='200').inc()
            return web.json_response({"tasks": tasks, "total": len(tasks)})

        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint='/tasks', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def get_task(self, request):
        """Get specific task"""
        task_id = request.match_info['task_id']

        try:
            task = self.kimi.tasks.get(task_id)
            if not task:
                REQUEST_COUNT.labels(method='GET', endpoint='/tasks/{id}', status='404').inc()
                return web.json_response({"error": "Task not found"}, status=404)

            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "dependencies": task.dependencies,
                "human_approval_required": task.human_approval_required,
                "metadata": task.metadata
            }

            REQUEST_COUNT.labels(method='GET', endpoint='/tasks/{id}', status='200').inc()
            return web.json_response(task_data)

        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint='/tasks/{id}', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def create_task(self, request):
        """Create a new task"""
        try:
            data = await request.json()

            # Validate required fields
            if not data.get('title'):
                return web.json_response({"error": "Title is required"}, status=400)

            # Parse priority
            priority_str = data.get('priority', 'medium')
            try:
                priority = TaskPriority(priority_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid priority: {priority_str}"},
                    status=400
                )

            # Parse due date if provided
            due_date = None
            if data.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(data['due_date'])
                except ValueError:
                    return web.json_response(
                        {"error": "Invalid due_date format. Use ISO format."},
                        status=400
                    )

            # Create task
            task = await self.kimi.create_task(
                title=data['title'],
                description=data.get('description', ''),
                priority=priority,
                assigned_to=data.get('assigned_to', 'kimi'),
                due_date=due_date,
                dependencies=data.get('dependencies', []),
                human_approval_required=data.get('human_approval_required', False),
                metadata=data.get('metadata', {})
            )

            TASK_COUNT.labels(priority=priority.value, status='created').inc()
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks', status='201').inc()

            return web.json_response({
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "message": "Task created successfully"
            }, status=201)

        except json.JSONDecodeError:
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks', status='400').inc()
            return web.json_response({"error": "Invalid JSON"}, status=400)

        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def execute_task(self, request):
        """Execute a specific task"""
        task_id = request.match_info['task_id']

        try:
            success = await self.kimi.execute_task(task_id)

            if success:
                REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/execute', status='200').inc()
                return web.json_response({
                    "message": "Task executed successfully",
                    "task_id": task_id
                })
            else:
                REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/execute', status='400').inc()
                return web.json_response({
                    "error": "Task execution failed",
                    "task_id": task_id
                }, status=400)

        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/execute', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def approve_task(self, request):
        """Approve a task requiring human approval"""
        task_id = request.match_info['task_id']

        try:
            task = self.kimi.tasks.get(task_id)
            if not task:
                return web.json_response({"error": "Task not found"}, status=404)

            # Remove approval requirement and execute
            task.human_approval_required = False
            task.status = TaskStatus.PENDING

            success = await self.kimi.execute_task(task_id)

            REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/approve', status='200').inc()
            return web.json_response({
                "message": "Task approved and executed",
                "task_id": task_id,
                "success": success
            })

        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/approve', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def deny_task(self, request):
        """Deny a task requiring human approval"""
        task_id = request.match_info['task_id']

        try:
            data = await request.json()
            reason = data.get('reason', 'No reason provided')

            task = self.kimi.tasks.get(task_id)
            if not task:
                return web.json_response({"error": "Task not found"}, status=404)

            # Mark task as cancelled
            task.status = TaskStatus.CANCELLED
            task.metadata['denial_reason'] = reason
            task.metadata['denied_at'] = datetime.now().isoformat()

            REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/deny', status='200').inc()
            return web.json_response({
                "message": "Task denied",
                "task_id": task_id,
                "reason": reason
            })

        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/tasks/{id}/deny', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def human_checkin(self, request):
        """Process human checkin"""
        try:
            data = await request.json()

            # Update context based on checkin data
            self.kimi.context.last_human_checkin = datetime.now()

            if 'objectives_update' in data:
                self.kimi.context.objectives = data['objectives_update']

            if 'constraints_update' in data:
                self.kimi.context.constraints = data['constraints_update']

            # Log the checkin
            self.kimi.decision_history.append({
                "type": "human_checkin",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })

            REQUEST_COUNT.labels(method='POST', endpoint='/checkin', status='200').inc()
            return web.json_response({
                "message": "Checkin processed successfully",
                "next_checkin": (datetime.now() +
                               timedelta(hours=self.kimi.config['human_checkin_interval_hours'])).isoformat()
            })

        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/checkin', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def get_next_actions(self, request):
        """Get recommended next actions"""
        try:
            actions = await self.kimi.get_next_actions()
            REQUEST_COUNT.labels(method='GET', endpoint='/next-actions', status='200').inc()
            return web.json_response({"actions": actions})

        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint='/next-actions', status='500').inc()
            return web.json_response({"error": str(e)}, status=500)

    async def dashboard(self, request):
        """Serve dashboard HTML"""
        dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Kimi Instruct Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric { text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007acc; }
        .metric-label { color: #666; margin-top: 5px; }
        .task-list { margin-top: 20px; }
        .task { padding: 10px; border-left: 4px solid #007acc; margin: 5px 0; background: #f9f9f9; }
        .task.critical { border-left-color: #ff4444; }
        .task.high { border-left-color: #ff8800; }
        .task.medium { border-left-color: #00aa44; }
        .refresh-btn { background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #005a99; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1 class="header">🤖 Kimi Instruct Dashboard</h1>
            <p style="text-align: center; color: #666;">Hybrid AI Project Manager for LabVerse Monitoring</p>
            <div style="text-align: center;">
                <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh</button>
            </div>
        </div>

        <div class="card">
            <h2>Project Status</h2>
            <div class="status-grid" id="status-grid">
                <!-- Status metrics will be loaded here -->
            </div>
        </div>

        <div class="card">
            <h2>Active Tasks</h2>
            <div class="task-list" id="task-list">
                <!-- Tasks will be loaded here -->
            </div>
        </div>

        <div class="card">
            <h2>Next Actions</h2>
            <div id="next-actions">
                <!-- Next actions will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        async function loadDashboard() {
            try {
                // Load status
                const statusResponse = await fetch('/status');
                const status = await statusResponse.json();

                // Load tasks
                const tasksResponse = await fetch('/tasks');
                const tasks = await tasksResponse.json();

                // Load next actions
                const actionsResponse = await fetch('/next-actions');
                const actions = await actionsResponse.json();

                // Update status grid
                const statusGrid = document.getElementById('status-grid');
                statusGrid.innerHTML = `
                    <div class="metric">
                        <div class="metric-value">${status.task_summary.completion_percentage.toFixed(1)}%</div>
                        <div class="metric-label">Progress</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${status.task_summary.total}</div>
                        <div class="metric-label">Total Tasks</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${status.task_summary.completed}</div>
                        <div class.metric-label">Completed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${status.task_summary.blocked}</div>
                        <div class="metric-label">Blocked</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${status.risk_level.toUpperCase()}</div>
                        <div class="metric-label">Risk Level</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">$${status.project_context.budget_remaining.toFixed(0)}</div>
                        <div class="metric-label">Budget Remaining</div>
                    </div>
                `;

                // Update task list
                const taskList = document.getElementById('task-list');
                taskList.innerHTML = tasks.tasks.slice(0, 10).map(task => `
                    <div class="task ${task.priority}">
                        <strong>${task.title}</strong>
                        <span style="background: #eee; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">${task.status}</span>
                        <br>
                        <small>${task.description}</small>
                    </div>
                `).join('');

                // Update next actions
                const nextActions = document.getElementById('next-actions');
                nextActions.innerHTML = actions.actions.map(action => `
                    <div class="task ${action.priority}">
                        <strong>${action.action.replace('_', ' ').toUpperCase()}</strong>
                        <br>
                        <small>${action.description}</small>
                    </div>
                `).join('') || '<p>No immediate actions required.</p>';

            } catch (error) {
                console.error('Failed to load dashboard:', error);
                document.getElementById('status-grid').innerHTML = '<p>Failed to load status</p>';
            }
        }

        // Load dashboard on page load
        window.onload = loadDashboard;

        // Auto-refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
        """

        return web.Response(text=dashboard_html, content_type='text/html')

async def create_app():
    """Create and configure the web application"""
    service = KimiService()
    return service.app

def main():
    """Main entry point"""
    import os

    host = os.getenv('KIMI_HOST', '0.0.0.0')
    port = int(os.getenv('KIMI_PORT', 8084))

    print(f"🤖 Starting Kimi Instruct on {host}:{port}")

    web.run_app(
        create_app(),
        host=host,
        port=port,
        access_log_format='%a %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
    )

if __name__ == '__main__':
    main()
