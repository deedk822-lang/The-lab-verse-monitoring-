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

from .core import KimiInstruct, TaskPriority as Priority, TaskStatus

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
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
        def labels(self, *args, **kwargs): return self
        def set(self, *args, **kwargs): pass
    
    def generate_latest(): return b"# Prometheus not available"
    CONTENT_TYPE_LATEST = 'text/plain'

try:
    from aiohttp_cors import setup as cors_setup, ResourceOptions
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Configure logging
logger = logging.getLogger('kimi_instruct')

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: Priority
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'priority': self.priority.value
        }

class AIEngine:
    """Production AI Engine with real provider integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self.session = None
        self.provider_config = self._load_provider_config()
        self._initialize_providers()
    
    def _load_provider_config(self) -> Dict[str, Any]:
        config_path = Path("config/ai_providers.yaml")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load AI provider config: {e}")
        return {}

    def _initialize_providers(self):
        for env_key, provider_name in [
            ("OPENAI_API_KEY", "openai"),
            ("DASHSCOPE_API_KEY", "dashscope"),
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("MOONSHOT_API_KEY", "moonshot"),
            ("OPENROUTER_API_KEY", "openrouter")
        ]:
            if os.getenv(env_key):
                self.providers[provider_name] = {"api_key": os.getenv(env_key)}
                if provider_name == "openai":
                    self.providers[provider_name].update({
                        "base_url": "https://api.openai.com/v1/chat/completions",
                        "model": "gpt-3.5-turbo"
                    })
                elif provider_name == "dashscope":
                    self.providers[provider_name].update({
                        "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                        "model": "qwen-turbo"
                    })
                elif provider_name == "openrouter":
                    self.providers[provider_name].update({
                        "base_url": "https://openrouter.ai/api/v1/chat/completions"
                    })
    
    async def get_session(self):
        if not self.session:
            self.session = ClientSession(timeout=ClientTimeout(total=30))
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def analyze_task(self, task: Task) -> Dict[str, Any]:
        if not self.providers:
            return self._heuristic_analysis(task)
        
        prompt = f"Analyze: {task.title}"
        
        try:
            if "openrouter" in self.providers and self.provider_config.get("openrouter"):
                conf = self.provider_config["openrouter"]
                for model in [conf.get("primary")] + conf.get("fallbacks", []):
                    try:
                        resp = await self._call_openrouter(model, prompt)
                        return self._parse_ai_response(resp)
                    except: continue

            for provider in self.provider_config.get("direct_providers", ["dashscope", "openai"]):
                if provider in self.providers:
                    try:
                        resp = await self._call_provider(provider, prompt)
                        return self._parse_ai_response(resp)
                    except: continue
            
            return self._heuristic_analysis(task)
        except:
            return self._heuristic_analysis(task)

    async def _call_provider(self, name, prompt):
        if name == "openai": return await self._call_openai(await self.get_session(), self.providers[name], prompt)
        if name == "dashscope": return await self._call_dashscope(await self.get_session(), self.providers[name], prompt)
        return ""

    async def _call_openai(self, session, provider, prompt):
        async with session.post(provider["base_url"], headers={"Authorization": f"Bearer {provider['api_key']}"},
                               json={"model": provider["model"], "messages": [{"role": "user", "content": prompt}]}) as resp:
            if resp.status == 200: return (await resp.json())["choices"][0]["message"]["content"]
            raise Exception("OpenAI error")

    async def _call_dashscope(self, session, provider, prompt):
        async with session.post(provider["base_url"], headers={"Authorization": f"Bearer {provider['api_key']}"},
                               json={"model": provider["model"], "input": {"messages": [{"role": "user", "content": prompt}]}}) as resp:
            if resp.status == 200: return (await resp.json())["output"]["choices"][0]["message"]["content"]
            raise Exception("DashScope error")

    async def _call_openrouter(self, model, prompt):
        provider = self.providers["openrouter"]
        async with (await self.get_session()).post(provider["base_url"], headers={"Authorization": f"Bearer {provider['api_key']}"},
                                                   json={"model": model, "messages": [{"role": "user", "content": prompt}]}) as resp:
            if resp.status == 200: return (await resp.json())["choices"][0]["message"]["content"]
            raise Exception("OpenRouter error")

    def _parse_ai_response(self, resp):
        return json.loads(resp)

    def _heuristic_analysis(self, task):
        return {"complexity": 0.5, "risk": "medium"}

def default_serializer(o):
    if isinstance(o, (datetime, date)): return o.isoformat()
    if isinstance(o, Enum): return o.value
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

async def handle_status(request):
    kimi = request.app.get('kimi')
    if kimi is None:
        kimi = KimiInstruct()
    report = await kimi.get_status_report()
    return web.json_response(report, dumps=lambda x: json.dumps(x, default=default_serializer))

async def handle_create_task(request):
    try:
        kimi = request.app.get('kimi')
        if kimi is None:
            kimi = KimiInstruct()
        data = await request.json()
        if 'title' not in data:
            return web.json_response({'error': 'title is required'}, status=400)
        task = await kimi.create_task(
            title=data['title'],
            description=data.get('description', ''),
            priority=Priority(data.get('priority', 'medium')),
            assigned_to=data.get('assigned_to', 'kimi'),
            human_approval_required=data.get('human_approval_required', False)
        )
        return web.json_response({'task_id': task.id}, status=201)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

async def handle_health(request):
    return web.json_response({"status": "healthy"})

class KimiInstructService:
    def __init__(self):
        self.kimi_instance = KimiInstruct()
        self.app = web.Application()
        self.app['kimi'] = self.kimi_instance
        self.setup_routes()

    @property
    def kimi(self):
        return self.kimi_instance

    def setup_routes(self):
        self.app.router.add_get('/health', self.health)
        self.app.router.add_get('/status', self.get_status)
        self.app.router.add_post('/tasks', self.create_task)

    async def health(self, request): return await handle_health(request)

    async def get_status(self, request):
        if 'kimi' not in request.app: request.app['kimi'] = self.kimi
        return await handle_status(request)
        
    async def create_task(self, request):
        if 'kimi' not in request.app: request.app['kimi'] = self.kimi
        return await handle_create_task(request)
        
    async def get_status_report(self): return await self.kimi.get_status_report()

KimiService = KimiInstructService
