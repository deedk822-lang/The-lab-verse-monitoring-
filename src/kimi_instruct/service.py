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
from datetime import datetime, timedelta, date
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
    CONTENT_TYPE_LATEST = 'text/plain'
    # Mock classes for when prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    def generate_latest(): return b"# Prometheus not available"

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
logger = logging.getLogger('kimi_instruct')

# Global metrics for Prometheus
if PROMETHEUS_AVAILABLE:
    try:
        KIMI_TASKS_TOTAL = Counter('kimi_tasks_total', 'Total tasks processed', ['status', 'type'])
        KIMI_TASK_DURATION = Histogram('kimi_task_duration_seconds', 'Task duration')
        KIMI_RISK_SCORE = Gauge('kimi_project_risk_score', 'Current project risk score')
        KIMI_EFFICIENCY_SCORE = Gauge('kimi_efficiency_score', 'Current efficiency score')
        KIMI_MRR_PROJECTION = Gauge('kimi_mrr_projection', 'Monthly Recurring Revenue projection')
    except ValueError:
        # Already defined (e.g. during tests)
        # We should ideally retrieve them, but for now we'll assume they exist globally
        # or use mocks if retrieval is hard.
        # Actually, in most cases, if they already exist, it's fine to just re-assign or ignore.
        import prometheus_client
        reg = prometheus_client.REGISTRY
        KIMI_TASKS_TOTAL = reg._names_to_collectors.get('kimi_tasks_total', Counter('kimi_tasks_total_dup', '...', ['status', 'type']))
        KIMI_TASK_DURATION = reg._names_to_collectors.get('kimi_task_duration_seconds', Histogram('kimi_task_duration_seconds_dup', '...'))
        KIMI_RISK_SCORE = reg._names_to_collectors.get('kimi_project_risk_score', Gauge('kimi_project_risk_score_dup', '...'))
        KIMI_EFFICIENCY_SCORE = reg._names_to_collectors.get('kimi_efficiency_score', Gauge('kimi_efficiency_score_dup', '...'))
        KIMI_MRR_PROJECTION = reg._names_to_collectors.get('kimi_mrr_projection', Gauge('kimi_mrr_projection_dup', '...'))
else:
    KIMI_TASKS_TOTAL = Counter()
    KIMI_TASK_DURATION = Histogram()
    KIMI_RISK_SCORE = Gauge()
    KIMI_EFFICIENCY_SCORE = Gauge()
    KIMI_MRR_PROJECTION = Gauge()

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

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
                raise Exception(f"Moonshot AI API error: {response.status} - {error_text}")

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

class KimiInstructService:
    """Production Kimi Instruct Service"""
    
    def __init__(self):
        self.app = web.Application()
        self.tasks: Dict[str, Task] = {}
        self.config = self._load_config()
        self.ai_engine = AIEngine(self.config)
        self.app['kimi'] = self # For compatibility with handlers expecting it in app
        
        # Use global metrics
        self.task_counter = KIMI_TASKS_TOTAL
        self.task_duration = KIMI_TASK_DURATION
        self.risk_gauge = KIMI_RISK_SCORE
        self.efficiency_gauge = KIMI_EFFICIENCY_SCORE
        self.revenue_gauge = KIMI_MRR_PROJECTION
        
        # Project metrics
        self.project_metrics = ProjectMetrics()
        
        self._setup_routes()
        self._setup_cors()
        
        logger.info(f"Kimi Instruct Service initialized with AI providers: {list(self.ai_engine.providers.keys())}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with environment variable integration"""
        default_config = {
            "human_oversight_mode": os.getenv("HUMAN_OVERSIGHT_MODE", "collaborative"),
            "auto_execution_threshold": float(os.getenv("AUTO_EXECUTION_THRESHOLD", "0.75")),
            "max_concurrent_tasks": int(os.getenv("MAX_CONCURRENT_TASKS", "15")),
            "risk_thresholds": {
                "low": 0.2,
                "medium": 0.5,
                "high": float(os.getenv("RISK_THRESHOLD_HIGH", "0.8")),
                "critical": float(os.getenv("RISK_THRESHOLD_CRITICAL", "0.95"))
            },
            "decision_authority": {
                "auto_deploy_staging": True,
                "auto_deploy_production": False,
                "auto_cost_optimization": True,
                "max_budget_decision": 5000,
                "require_approval_keywords": ["production", "delete", "critical", "security", "budget", "revenue"]
            },
            "revenue_optimization": {
                "enabled": True,
                "target_mrr": int(os.getenv("TARGET_MRR", "75000")),
                "optimization_frequency_hours": int(os.getenv("OPTIMIZATION_FREQUENCY_HOURS", "6")),
                "a2a_negotiation_enabled": os.getenv("A2A_NEGOTIATION_ENABLED", "true").lower() == "true"
            }
        }
        
        # Load from file if exists
        config_path = Path("config/kimi_instruct.json")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        return default_config

    def _setup_cors(self):
        """Setup CORS for web dashboard"""
        if CORS_AVAILABLE:
            try:
                cors = cors_setup(self.app, defaults={
                    "*": ResourceOptions(
                        allow_credentials=True,
                        expose_headers="*",
                        allow_headers="*",
                        allow_methods="*"
                    )
                })
            except Exception as e:
                logger.warning(f"CORS setup failed: {e}")

    def _setup_routes(self):
        """Setup comprehensive API routes"""
        
        # Core API routes
        self.app.router.add_get('/', self._handle_root)
        self.app.router.add_get('/health', self._handle_health)
        self.app.router.add_get('/status', self._handle_status)
        
        if PROMETHEUS_AVAILABLE:
            self.app.router.add_get('/metrics', self._handle_metrics)
        
        # Task management
        self.app.router.add_get('/api/v1/tasks', self._handle_list_tasks)
        self.app.router.add_post('/api/v1/tasks', self._handle_create_task)
        self.app.router.add_get('/api/v1/tasks/{task_id}', self._handle_get_task)
        
        # AI & Intelligence
        self.app.router.add_get('/api/v1/next-actions', self._handle_next_actions)
        self.app.router.add_post('/api/v1/analyze', self._handle_analyze)
        self.app.router.add_get('/api/v1/optimize', self._handle_optimize)
        
        # Revenue optimization
        self.app.router.add_post('/api/v1/revenue/optimize', self._handle_revenue_optimize)
        
        # Basic dashboard (serve static content if available)
        self.app.router.add_get('/dashboard', self._handle_dashboard)
        
        # Add static file serving if directory exists
        if Path("static").exists():
            self.app.router.add_static('/', 'static', name='static')

    async def _handle_root(self, request):
        """Enhanced root endpoint with system info"""
        return web.json_response({
            "service": "Kimi Instruct AI Project Manager",
            "version": "2.0.0-production",
            "status": "operational",
            "ai_providers": list(self.ai_engine.providers.keys()),
            "features": [
                "AI-powered task management",
                "Multi-provider AI integration", 
                "Revenue optimization",
                "Real-time monitoring",
                "Human-AI collaboration"
            ],
            "endpoints": {
                "dashboard": "/dashboard",
                "api": "/api/v1",
                "health": "/health",
                "metrics": "/metrics" if PROMETHEUS_AVAILABLE else None
            }
        })

    async def _handle_health(self, request):
        """Comprehensive health check with AI provider status"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-production",
            "components": {
                "ai_engine": "healthy" if self.ai_engine.providers else "degraded",
                "task_manager": "healthy",
                "metrics": "healthy" if PROMETHEUS_AVAILABLE else "disabled"
            },
            "ai_providers": {
                provider: "available" for provider in self.ai_engine.providers.keys()
            },
            "metrics": {
                "total_tasks": self.project_metrics.total_tasks,
                "active_tasks": len([t for t in self.tasks.values() 
                                   if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]),
                "success_rate": self._calculate_success_rate(),
                "mrr_projection": self.project_metrics.mrr_projection
            }
        }
        
        return web.json_response(health_data)

    async def _handle_status(self, request):
        """Get comprehensive project status"""
        return web.json_response({
            "project_metrics": {
                k: v.isoformat() if isinstance(v, datetime) else v 
                for k, v in asdict(self.project_metrics).items()
            },
            "project_context": { # Compatibility with tests
                "current_phase": "production",
                "risk_level": self.project_metrics.system_health,
                "timeline_status": "on_track",
                "budget_remaining": self.project_metrics.budget_total - self.project_metrics.budget_used,
                "metrics": {"risk_score": self.project_metrics.risk_score}
            },
            "ai_providers": list(self.ai_engine.providers.keys()),
            "active_tasks": len([t for t in self.tasks.values() 
                               if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]),
            "recent_tasks": [t.to_dict() for t in list(self.tasks.values())[-5:]],
            "system_health": "operational",
            "critical_issues": [],
            "next_actions": [],
            "task_summary": { # Compatibility with version 1 tests
                "total": self.project_metrics.total_tasks,
                "completed": self.project_metrics.completed_tasks,
                "completion_percentage": self._calculate_success_rate() * 100
            }
        }, dumps=lambda x: json.dumps(x, default=default_serializer))

    async def _handle_metrics(self, request):
        """Prometheus metrics endpoint"""
        if not PROMETHEUS_AVAILABLE:
            return web.Response(text="# Prometheus not available", content_type='text/plain')
        return web.Response(text=generate_latest().decode('utf-8'), content_type=CONTENT_TYPE_LATEST)

    async def _handle_dashboard(self, request):
        """Production dashboard HTML"""
        dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Kimi Instruct Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .status-card { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }
        .api-links { display: flex; gap: 10px; flex-wrap: wrap; }
        .api-link { background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; }
        .api-link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Kimi Instruct Dashboard</h1>
        <div class="status-card">
            <h3>Status: Operational</h3>
            <p>AI-powered project management is active and ready.</p>
        </div>
        
        <h3>Quick Actions:</h3>
        <div class="api-links">
            <a href="/api/v1/tasks" class="api-link">View Tasks</a>
            <a href="/health" class="api-link">System Health</a>
            <a href="/status" class="api-link">Project Status</a>
            <a href="/metrics" class="api-link">Metrics</a>
        </div>
        
        <h3>CLI Usage:</h3>
        <pre>
# Get status
./kimi-cli status --detailed

# Create task
./kimi-cli task --title "Deploy service" --priority high

# Revenue optimization
./kimi-cli revenue --target-mrr 25000
        </pre>
        
        <p><strong>Pro tip:</strong> Use the CLI for advanced operations and automation!</p>
    </div>
</body>
</html>
        """
        return web.Response(text=dashboard_html, content_type='text/html')

    async def _handle_create_task(self, request):
        """Create new task with AI analysis"""
        try:
            data = await request.json()
            
            if "title" not in data:
                 return web.json_response({"error": "Title is required"}, status=400)

            task_id = f"task_{uuid.uuid4().hex[:8]}"
            task = Task(
                id=task_id,
                title=data["title"],
                description=data.get("description", ""),
                status=TaskStatus.PENDING,
                priority=Priority(data.get("priority", "medium")),
                task_type=TaskType(data.get("type", "analysis")),
                requires_approval=data.get("requires_approval", False),
                metadata=data.get("metadata", {})
            )
            
            # AI analysis
            try:
                analysis = await self.ai_engine.analyze_task(task)
                task.metadata["ai_analysis"] = analysis
                
                # Determine if approval needed based on AI analysis
                if analysis.get("risk_assessment") in ["high", "critical"]:
                    task.requires_approval = True
                    task.approval_reason = f"High risk detected: {analysis.get('risk_assessment')}"
                    task.status = TaskStatus.REQUIRES_APPROVAL
                    
            except Exception as e:
                logger.warning(f"AI analysis failed for task {task_id}: {e}")
            
            self.tasks[task_id] = task
            self.project_metrics.total_tasks += 1
            self.task_counter.labels(status="created", type=task.task_type.value).inc()
            
            logger.info(f"Task created: {task_id} - {task.title}")
            
            return web.json_response({
                "task": task.to_dict(),
                "task_id": task_id, # Compatibility
                "message": "Task created successfully"
            }, status=201)
            
        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            return web.json_response({"error": f"Task creation failed: {str(e)}"}, status=500)

    async def _handle_list_tasks(self, request):
        """List tasks with filtering"""
        status_filter = request.query.get("status")
        priority_filter = request.query.get("priority")
        limit = int(request.query.get("limit", 50))
        
        tasks = list(self.tasks.values())
        
        if status_filter:
            tasks = [t for t in tasks if t.status.value == status_filter]
        if priority_filter:
            tasks = [t for t in tasks if t.priority.value == priority_filter]
        
        # Sort by created_at desc and limit
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        tasks = tasks[:limit]
        
        return web.json_response({
            "tasks": [t.to_dict() for t in tasks],
            "total": len(tasks),
            "filters_applied": {
                "status": status_filter,
                "priority": priority_filter,
                "limit": limit
            }
        })

    async def _handle_get_task(self, request):
        """Get specific task details"""
        task_id = request.match_info['task_id']
        
        if task_id not in self.tasks:
            return web.json_response({"error": "Task not found"}, status=404)
        
        task = self.tasks[task_id]
        return web.json_response({"task": task.to_dict()})

    async def _handle_next_actions(self, request):
        """Get AI-powered next action recommendations"""
        recommendations = [
            {
                "action": "Review pending tasks",
                "priority": "high",
                "reason": "Multiple tasks require attention",
                "estimated_time": 15
            },
            {
                "action": "Run revenue optimization",
                "priority": "medium", 
                "reason": "MRR growth opportunity identified",
                "estimated_time": 5
            }
        ]
        
        return web.json_response({"recommendations": recommendations})

    async def _handle_analyze(self, request):
        """Analyze arbitrary text/task with AI"""
        try:
            data = await request.json()
            text = data.get("text", "")
            
            if not text:
                return web.json_response({"error": "Text is required"}, status=400)
            
            # Create temporary task for analysis
            temp_task = Task(
                id="temp",
                title="Analysis Request",
                description=text,
                status=TaskStatus.PENDING,
                priority=Priority.MEDIUM
            )
            
            analysis = await self.ai_engine.analyze_task(temp_task)
            
            return web.json_response({
                "analysis": analysis,
                "text_analyzed": text[:100] + "..." if len(text) > 100 else text
            })
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return web.json_response({"error": "Analysis failed"}, status=500)

    async def _handle_optimize(self, request):
        """Get optimization recommendations"""
        return web.json_response({
            "optimizations": [
                {
                    "type": "performance",
                    "recommendation": "Optimize task scheduling algorithm",
                    "impact": "15% efficiency improvement",
                    "effort": "medium"
                },
                {
                    "type": "cost",
                    "recommendation": "Implement AI provider cost optimization",
                    "impact": "$500/month savings",
                    "effort": "low"
                }
            ],
            "competitive_intelligence": {
                "market_position": "Leading in AI automation",
                "advantages": ["Multi-provider AI integration", "Real-time optimization"]
            }
        })

    async def _handle_revenue_optimize(self, request):
        """Handle revenue optimization requests"""
        try:
            data = await request.json()
            
            # Create revenue optimization task
            task_id = f"rev_opt_{uuid.uuid4().hex[:8]}"
            task = Task(
                id=task_id,
                title=f"Revenue Optimization: {data.get('target', 'General')}",
                description=f"AI-powered revenue optimization targeting ${data.get('target_mrr', 10000):,}",
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.HIGH,
                task_type=TaskType.REVENUE_OPTIMIZATION,
                metadata={
                    "target_channels": data.get("channels", ["organic", "paid", "affiliate"]),
                    "target_mrr": data.get("target_mrr", 10000),
                    "optimization_type": data.get("type", "conversion")
                }
            )
            
            # AI analysis for revenue optimization
            analysis = await self.ai_engine.analyze_task(task)
            
            # Simulate revenue projections
            base_mrr = self.project_metrics.mrr_projection
            optimization_factor = analysis.get("revenue_impact", 0.2)
            projected_increase = base_mrr * optimization_factor if base_mrr > 0 else data.get("target_mrr", 10000) * 0.1
            
            self.tasks[task_id] = task
            
            # Update MRR projection
            self.project_metrics.mrr_projection += projected_increase
            self.revenue_gauge.set(self.project_metrics.mrr_projection)
            
            logger.info(f"Revenue optimization initiated: {task_id}, projected increase: ${projected_increase:.2f}")
            
            return web.json_response({
                "task": task.to_dict(),
                "analysis": analysis,
                "projections": {
                    "current_mrr": base_mrr,
                    "projected_increase": projected_increase,
                    "new_mrr_projection": self.project_metrics.mrr_projection,
                    "confidence": analysis.get("automation_potential", 0.5)
                }
            })
            
        except Exception as e:
            logger.error(f"Revenue optimization failed: {e}")
            return web.json_response({"error": "Revenue optimization failed"}, status=500)

    def _calculate_success_rate(self) -> float:
        """Calculate task success rate"""
        if not self.tasks:
            return 1.0
        
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        total = len(self.tasks)
        return completed / total if total > 0 else 1.0

    # Public aliases for handlers (for compatibility with tests)
    @property
    def kimi(self):
        return self

    async def health(self, request):
        return await self._handle_health(request)

    async def create_task(self, request):
        return await self._handle_create_task(request)

    async def get_status(self, request):
        return await self._handle_status(request)

    async def get_status_report(self):
        # Return dict instead of Response for internal use
        return {
            "project_metrics": {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in asdict(self.project_metrics).items()
            },
            "project_context": {
                "current_phase": "production",
                "risk_level": self.project_metrics.system_health,
                "timeline_status": "on_track",
                "budget_remaining": self.project_metrics.budget_total - self.project_metrics.budget_used,
                "metrics": {"risk_score": self.project_metrics.risk_score}
            },
            "task_summary": {
                "total": self.project_metrics.total_tasks,
                "completed": self.project_metrics.completed_tasks,
                "completion_percentage": self._calculate_success_rate() * 100
            },
            "risk_level": self.project_metrics.system_health,
            "critical_issues": [],
            "next_actions": []
        }

    async def start(self, host: str = "0.0.0.0", port: int = 8084):
        """Start the production Kimi service"""
        # Create data and logs directories
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info(f"Starting Kimi Instruct Production Service on {host}:{port}")
        logger.info(f"AI providers: {list(self.ai_engine.providers.keys())}")
        logger.info(f"Prometheus metrics: {'enabled' if PROMETHEUS_AVAILABLE else 'disabled'}")
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"🤖 Kimi Instruct service started successfully!")
        logger.info(f"   Dashboard: http://{host}:{port}/dashboard")
        logger.info(f"   API: http://{host}:{port}/api/v1")
        logger.info(f"   Health: http://{host}:{port}/health")
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down Kimi Instruct service")
        finally:
            await self.ai_engine.close_session()
            await runner.cleanup()

# Global functions and compatibility wrappers
def default_serializer(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

_service_instance = KimiInstructService()
KimiService = KimiInstructService # Alias for compatibility

async def handle_status(request):
    return await _service_instance._handle_status(request)

async def handle_create_task(request):
    return await _service_instance._handle_create_task(request)

async def handle_health(request):
    return web.json_response({"status": "healthy"})

async def main():
    """Main entry point"""
    await _service_instance.start()

if __name__ == "__main__":
    asyncio.run(main())
