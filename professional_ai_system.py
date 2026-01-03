"""
Professional Full-Stack AI Generation System (2026 Standards)
Complete, production-ready implementation with no mock-ups.
"""

import asyncio
import aiohttp
import json
import yaml
import re
import subprocess
import shutil
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class SystemConfig:
    """Centralized configuration with validation"""
    api_key: str
    api_base_url: str = "https://api.moonshot.ai/v1"
    model_backend: str = "kimi-k2-thinking"
    model_frontend: str = "kimi-k2-thinking"
    max_retries: int = 3
    timeout_seconds: int = 300
    parallel_generation: bool = True
    auto_fix_enabled: bool = True
    security_scan_enabled: bool = True
    cost_limit_usd: float = 10.0
    log_level: str = "INFO"
    project_root: Path = Path("generated_project")

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("API key required")
        self.project_root = Path(self.project_root)

    def to_dict(self) -> Dict:
        return asdict(self)

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class SystemLogger:
    """Professional logging with context"""

    def __init__(self, config: SystemConfig):
        self.logger = logging.getLogger("FullStackGenerator")
        self.logger.setLevel(getattr(logging, config.log_level))

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(console)

        # File handler
        log_dir = config.project_root / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        file_handler = logging.FileHandler(
            log_dir / f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
        ))
        self.logger.addHandler(file_handler)

    def info(self, msg: str): self.logger.info(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def debug(self, msg: str): self.logger.debug(msg)

# ============================================================================
# COST TRACKING
# ============================================================================

class CostTracker:
    """Track and limit API costs"""

    # 2026 pricing (tokens in thousands)
    PRICING = {
        "kimi-k2-thinking": {"input": 0.015, "output": 0.06},  # per 1K tokens
    }

    def __init__(self, limit_usd: float):
        self.limit = limit_usd
        self.total_cost = 0.0
        self.calls = []

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a call"""
        pricing = self.PRICING.get(model, {"input": 0.01, "output": 0.03})
        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        return cost

    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record a call"""
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.total_cost += cost
        self.calls.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

        if self.total_cost > self.limit:
            raise ValueError(f"Cost limit exceeded: ${self.total_cost:.2f} > ${self.limit:.2f}")

    def get_report(self) -> Dict:
        return {
            "total_cost": round(self.total_cost, 2),
            "limit": self.limit,
            "calls": len(self.calls),
            "remaining_budget": round(self.limit - self.total_cost, 2)
        }

# ============================================================================
# ENHANCED CONTRACT PARSER
# ============================================================================

class ContractParser:
    """Parse contract and generate all type artifacts"""

    def __init__(self, contract_path: Path, logger: SystemLogger):
        self.contract_path = contract_path
        self.logger = logger
        self.contract = self._load_and_validate()
        self.types_dir = Path("generated_types")
        self.types_dir.mkdir(exist_ok=True)

    def _load_and_validate(self) -> Dict[str, Any]:
        """Load and validate contract schema"""
        if not self.contract_path.exists():
            raise FileNotFoundError(f"Contract not found: {self.contract_path}")

        with open(self.contract_path) as f:
            data = yaml.safe_load(f)

        # Validate required sections
        required = ["contract_version", "project", "backend", "frontend", "models"]
        missing = [r for r in required if r not in data]
        if missing:
            raise ValueError(f"Contract missing required sections: {missing}")

        self.logger.info(f"Loaded contract v{data['contract_version']}: {data['project']}")
        return data

    def generate_pydantic_models(self) -> str:
        """Generate complete Pydantic models with validation"""
        code = [
            "from pydantic import BaseModel, Field, EmailStr, validator",
            "from typing import List, Optional, Dict, Any",
            "from datetime import datetime",
            "from enum import Enum",
            "",
        ]

        for model_name, fields in self.contract['models'].items():
            code.append(f"class {model_name}(BaseModel):")

            for field_name, field_spec in fields.items():
                field_type = self._parse_field_type(field_spec)
                code.append(f"    {field_name}: {field_type}")

            code.append("")
            code.append("    class Config:")
            code.append("        json_schema_extra = {")
            code.append(f"            'example': {self._generate_example(model_name, fields)}")
            code.append("        }")
            code.append("")

        models_code = "\n".join(code)
        (self.types_dir / "pydantic_models.py").write_text(models_code)
        self.logger.info(f"Generated Pydantic models: {len(self.contract['models'])} classes")
        return models_code

    def _parse_field_type(self, field_spec: Any) -> str:
        """Parse field specification to Python type"""
        if isinstance(field_spec, str):
            mapping = {
                "string": "str",
                "number": "float",
                "integer": "int",
                "boolean": "bool",
                "email": "EmailStr",
                "datetime": "datetime",
            }

            # Handle arrays
            if field_spec.endswith("[]"):
                base = field_spec[:-2]
                inner = mapping.get(base, base)
                return f"List[{inner}]"

            return mapping.get(field_spec, "str")

        return "Any"

    def _generate_example(self, model_name: str, fields: Dict) -> str:
        """Generate example data for schema"""
        examples = {
            "string": "'example'",
            "number": "42.0",
            "integer": "42",
            "boolean": "true",
            "email": "'user@example.com'",
        }

        example = {}
        for field_name, field_spec in fields.items():
            if isinstance(field_spec, str):
                base_type = field_spec.replace("[]", "")
                example[field_name] = examples.get(base_type, "'example'")

        return json.dumps(example, indent=12)

    def generate_typescript_types(self) -> str:
        """Generate TypeScript interfaces and Zod schemas"""
        ts_code = []
        zod_code = ["import { z } from 'zod';", ""]

        for model_name, fields in self.contract['models'].items():
            # TypeScript interface
            ts_code.append(f"export interface {model_name} {{")

            # Zod schema
            zod_code.append(f"export const {model_name}Schema = z.object({{")

            for field_name, field_spec in fields.items():
                ts_type = self._map_ts_type(field_spec)
                zod_type = self._map_zod_type(field_spec)

                ts_code.append(f"  {field_name}: {ts_type};")
                zod_code.append(f"  {field_name}: {zod_type},")

            ts_code.append("}")
            ts_code.append("")
            zod_code.append("});")
            zod_code.append("")

        # Write files
        (self.types_dir / "types.ts").write_text("\n".join(ts_code))
        (self.types_dir / "schemas.ts").write_text("\n".join(zod_code))

        self.logger.info("Generated TypeScript types and Zod schemas")
        return "\n".join(ts_code)

    def _map_ts_type(self, field_spec: str) -> str:
        """Map to TypeScript type"""
        mapping = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "email": "string",
            "datetime": "string",
        }

        if field_spec.endswith("[]"):
            base = field_spec[:-2]
            inner = mapping.get(base, base)
            return f"{inner}[]"

        return mapping.get(field_spec, "any")

    def _map_zod_type(self, field_spec: str) -> str:
        """Map to Zod validator"""
        mapping = {
            "string": "z.string()",
            "number": "z.number()",
            "integer": "z.number().int()",
            "boolean": "z.boolean()",
            "email": "z.string().email()",
            "datetime": "z.string().datetime()",
        }

        if field_spec.endswith("[]"):
            base = field_spec[:-2]
            inner = mapping.get(base, "z.any()")
            return f"z.array({inner})"

        return mapping.get(field_spec, "z.any()")

    def generate_api_client(self) -> str:
        """Generate TypeScript API client"""
        client_code = [
            "import axios, { AxiosInstance } from 'axios';",
            "import * as Types from './types';",
            "",
            "export class ApiClient {",
            "  private client: AxiosInstance;",
            "",
            "  constructor(baseURL: string) {",
            "    this.client = axios.create({",
            "      baseURL,",
            "      headers: { 'Content-Type': 'application/json' }",
            "    });",
            "  }",
            ""
        ]

        # Generate methods from endpoints
        for endpoint, spec in self.contract['backend']['endpoints'].items():
            method = spec['method'].lower()
            response_type = spec.get('response', 'any')

            method_name = endpoint.split('/')[-1]

            if method == 'get':
                client_code.append(f"  async get{method_name.title()}(): Promise<Types.{response_type}> {{")
                client_code.append(f"    const {{ data }} = await this.client.get('{endpoint}');")
                client_code.append("    return data;")
                client_code.append("  }")
                client_code.append("")

            elif method == 'post':
                body_type = spec.get('body', 'any')
                client_code.append(f"  async post{method_name.title()}(body: Types.{body_type}): Promise<Types.{response_type}> {{")
                client_code.append(f"    const {{ data }} = await this.client.post('{endpoint}', body);")
                client_code.append("    return data;")
                client_code.append("  }")
                client_code.append("")

        client_code.append("}")

        api_client = "\n".join(client_code)
        (self.types_dir / "api-client.ts").write_text(api_client)
        self.logger.info("Generated API client")
        return api_client

    def generate_database_schema(self) -> str:
        """Generate SQL schema from models"""
        sql = ["-- Auto-generated database schema", ""]

        for model_name, fields in self.contract['models'].items():
            table_name = self._to_snake_case(model_name)
            sql.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
            sql.append("    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),")

            for field_name, field_spec in fields.items():
                if field_name != 'id':
                    sql_type = self._map_sql_type(field_spec)
                    sql.append(f"    {field_name} {sql_type},")

            sql.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            sql.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            sql.append(");")
            sql.append("")

        schema_sql = "\n".join(sql)
        (self.types_dir / "schema.sql").write_text(schema_sql)
        self.logger.info("Generated database schema")
        return schema_sql

    def _map_sql_type(self, field_spec: str) -> str:
        """Map to SQL type"""
        mapping = {
            "string": "TEXT",
            "number": "DECIMAL",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "email": "VARCHAR(255)",
            "datetime": "TIMESTAMP",
        }
        return mapping.get(field_spec.replace("[]", ""), "TEXT")

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

# ============================================================================
# PARALLEL GENERATION WITH QUALITY CONTROL
# ============================================================================

class ParallelGenerator:
    """Generate backend and frontend with advanced prompting"""

    def __init__(self, config: SystemConfig, contract: Dict, logger: SystemLogger, cost_tracker: CostTracker):
        self.config = config
        self.contract = contract
        self.logger = logger
        self.cost_tracker = cost_tracker

    async def generate_all(self) -> Tuple[str, str]:
        """Generate backend and frontend in parallel"""
        self.logger.info("Starting parallel generation...")

        if self.config.parallel_generation:
            backend_task = asyncio.create_task(self._generate_backend())

            # Wait for backend to get OpenAPI spec
            await asyncio.sleep(2)  # Give backend generation a head start

            frontend_task = asyncio.create_task(self._generate_frontend())

            backend_code, frontend_code = await asyncio.gather(backend_task, frontend_task)
        else:
            backend_code = await self._generate_backend()
            frontend_code = await self._generate_frontend()

        return backend_code, frontend_code

    async def _generate_backend(self) -> str:
        """Generate production FastAPI backend"""
        pydantic_models = Path("generated_types/pydantic_models.py").read_text()

        prompt = self._create_backend_prompt(pydantic_models)

        response = await self._call_api(prompt, self.config.model_backend)

        self.logger.info("Backend generation complete")
        return response

    def _create_backend_prompt(self, pydantic_models: str) -> str:
        """Create optimized backend prompt"""
        return f"""Generate a PRODUCTION-READY FastAPI backend following this exact contract:

CONTRACT:
```yaml
{yaml.dump(self.contract, default_flow_style=False)}
```

PYDANTIC MODELS (USE EXACTLY AS-IS):
```python
{pydantic_models}
```

REQUIREMENTS (2026 Industry Standards):

1. **Architecture**:
   - FastAPI 0.110+ with Pydantic v2
   - Repository pattern for data access
   - Dependency injection for services
   - SQLAlchemy 2.0 async ORM

2. **Security**:
   - Rate limiting (slowapi: 100/hour per IP)
   - Input validation (Pydantic + custom validators)
   - CORS (configurable origins from env)
   - SQL injection prevention (parameterized queries)
   - XSS protection (escape outputs)

3. **Integrations** (implement these EXACTLY):
   {self._format_integrations()}

4. **Error Handling**:
   - Custom exception handlers
   - Structured error responses
   - Logging with correlation IDs

5. **Testing**:
   - pytest with async support
   - 80%+ code coverage
   - Integration tests for all endpoints
   - Mock external APIs

6. **Documentation**:
   - OpenAPI 3.1 spec at /docs
   - README with setup instructions

OUTPUT FORMAT:
Provide complete, working code in this structure:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with all routes
│   ├── models.py        # Use provided Pydantic models
│   ├── database.py      # SQLAlchemy setup
│   ├── repositories.py  # Data access layer
│   ├── services.py      # Business logic
│   └── integrations/    # External API clients
│       ├── hubspot.py
│       ├── mailchimp.py
│       └── ollama.py
├── tests/
│   ├── test_endpoints.py
│   ├── test_services.py
│   └── conftest.py
├── requirements.txt
├── Dockerfile
└── README.md
```

Output each file as:
```path/to/file.py
code here
```"""

    def _format_integrations(self) -> str:
        """Format integration requirements"""
        integrations = self.contract.get('integrations', [])
        details = {
            'hubspot': "- Sync registrations to HubSpot Contacts via REST API\n   - Error handling for API failures\n   - Retry logic with exponential backoff",
            'mailchimp': "- Subscribe emails to newsletter list\n   - Handle duplicate subscriptions gracefully\n   - Async processing (don't block endpoint)",
            'ollama': "- Enrich speaker bios with AI-generated insights\n   - Local Ollama endpoint (configurable)\n   - Fallback to original bio if unavailable"
        }

        return "\n".join(f"   - {integration.upper()}: {details.get(integration, 'Implement as specified')}"
                        for integration in integrations)

    async def _generate_frontend(self) -> str:
        """Generate production Next.js frontend"""
        ts_types = Path("generated_types/types.ts").read_text()
        api_client = Path("generated_types/api-client.ts").read_text()

        prompt = self._create_frontend_prompt(ts_types, api_client)

        response = await self._call_api(prompt, self.config.model_frontend)

        self.logger.info("Frontend generation complete")
        return response

    def _create_frontend_prompt(self, ts_types: str, api_client: str) -> str:
        """Create optimized frontend prompt"""
        return f"""Generate a PRODUCTION-READY Next.js 15 frontend following this contract:

CONTRACT:
```yaml
{yaml.dump(self.contract, default_flow_style=False)}
```

TYPESCRIPT TYPES (USE EXACTLY):
```typescript
{ts_types}
```

API CLIENT (USE THIS):
```typescript
{api_client}
```

REQUIREMENTS (2026 Standards):

1. **Framework**:
   - Next.js 15 App Router
   - React 19
   - TypeScript strict mode

2. **Styling**:
   - Tailwind CSS 4.0
   - shadcn/ui components
   - Responsive design (mobile-first)

3. **Data Fetching**:
   - TanStack Query v5 for client state
   - Server Actions for mutations
   - Optimistic updates

4. **Forms**:
   - react-hook-form
   - Zod validation (generated schemas)
   - Accessible forms (ARIA labels)

5. **Performance**:
   - Image optimization (next/image)
   - Code splitting (dynamic imports)
   - Suspense boundaries

6. **Testing**:
   - Jest + React Testing Library
   - Unit tests for components
   - Integration tests for flows

OUTPUT STRUCTURE:
```
frontend/
├── app/
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── register/
│       └── page.tsx     # Registration page
├── components/
│   ├── ui/              # shadcn components
│   ├── Hero.tsx
│   ├── SpeakersGrid.tsx
│   ├── EventSchedule.tsx
│   └── RegistrationForm.tsx
├── lib/
│   ├── api-client.ts    # Use provided client
│   └── utils.ts
├── __tests__/
│   └── components/
├── package.json
└── next.config.js
```

Output each file as:
```path/to/file.tsx
code here
```"""

    async def _call_api(self, prompt: str, model: str) -> str:
        """Call API with retries and cost tracking"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        # Estimate tokens (rough: 4 chars per token)
        input_tokens = len(prompt) // 4

        for attempt in range(self.config.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    data = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                        "max_tokens": 16000
                    }

                    async with session.post(
                        f"{self.config.api_base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as response:
                        result = await response.json()

                        if response.status != 200:
                            raise Exception(f"API error: {result}")

                        content = result['choices'][0]['message']['content']
                        output_tokens = len(content) // 4

                        self.cost_tracker.track_call(model, input_tokens, output_tokens)

                        return content

            except asyncio.TimeoutError:
                self.logger.warning(f"API timeout on attempt {attempt + 1}/{self.config.max_retries}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                self.logger.error(f"API call failed: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

# ============================================================================
# PROFESSIONAL FILE PARSER
# ============================================================================

class FileParser:
    """Parse generated markdown to project structure"""

    def __init__(self, project_dir: Path, logger: SystemLogger):
        self.project_dir = project_dir
        self.logger = logger

    def parse_to_files(self, markdown: str, subdir: str) -> List[Path]:
        """Parse markdown code blocks to files"""
        # Enhanced regex: matches ```filepath or ```language filepath
        pattern = r'```(?:[\w]+\s+)?([^\n]+)\n(.*?)```'

        matches = re.findall(pattern, markdown, re.DOTALL)
        created_files = []

        for filepath, code in matches:
            filepath = filepath.strip()

            # Skip if it's just a language identifier
            if filepath in ['python', 'typescript', 'javascript', 'yaml', 'json', 'bash', 'sql']:
                continue

            # Create full path
            full_path = self.project_dir / subdir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            full_path.write_text(code.strip())
            created_files.append(full_path)

            self.logger.debug(f"Created: {full_path}")

        self.logger.info(f"Parsed {len(created_files)} files to {subdir}/")
        return created_files

    def generate_dependencies(self):
        """Generate package.json and requirements.txt"""
        # Backend requirements
        backend_reqs = [
            "fastapi==0.110.0",
            "uvicorn[standard]==0.27.0",
            "sqlalchemy==2.0.27",
            "pydantic==2.6.1",
            "python-multipart==0.0.9",
            "python-dotenv==1.0.1",
            "slowapi==0.1.9",
            "httpx==0.26.0",
            "pytest==8.0.0",
            "pytest-asyncio==0.23.5",
            "pytest-cov==4.1.0",
        ]

        backend_dir = self.project_dir / "backend"
        backend_dir.mkdir(exist_ok=True)
        (backend_dir / "requirements.txt").write_text("\n".join(backend_reqs))

        # Frontend package.json
        package_json = {
            "name": "frontend",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "test": "jest"
            },
            "dependencies": {
                "next": "^15.0.0",
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "@tanstack/react-query": "^5.0.0",
                "axios": "^1.6.0",
                "zod": "^3.22.0",
                "react-hook-form": "^7.50.0",
                "@hookform/resolvers": "^3.3.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^19.0.0",
                "typescript": "^5.3.0",
                "tailwindcss": "^4.0.0",
                "jest": "^29.7.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^6.0.0"
            }
        }

        frontend_dir = self.project_dir / "frontend"
        frontend_dir.mkdir(exist_ok=True)
        (frontend_dir / "package.json").write_text(json.dumps(package_json, indent=2))

        self.logger.info("Generated dependency files")

# ============================================================================
# ADVANCED VALIDATOR WITH AUTO-FIX
# ============================================================================

class AdvancedValidator:
    """Comprehensive validation and auto-fixing"""

    def __init__(self, project_dir: Path, config: SystemConfig, logger: SystemLogger):
        self.project_dir = project_dir
        self.config = config
        self.logger = logger
        self.results = {}

    def run_all_checks(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        self.logger.info("Running validation suite...")

        self.results = {
            "security": self._run_security_scan(),
            "linting": self._run_linters(),
            "tests": self._run_tests(),
            "coverage": self._check_coverage(),
            "docker": self._validate_docker()
        }

        all_passed = all(r.get("status") == "pass" for r in self.results.values())
        self.results["overall"] = "pass" if all_passed else "fail"

        return self.results

    def _run_security_scan(self) -> Dict:
        """Run Bandit security scan"""
        if not self.config.security_scan_enabled:
            return {"status": "skipped"}

        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.project_dir / "backend"), "-f", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {"status": "pass", "issues": 0}

            issues = json.loads(result.stdout).get("results", [])
            high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]

            return {
                "status": "fail" if high_severity else "pass",
                "issues": len(issues),
                "high_severity": len(high_severity),
                "details": high_severity[:5]  # First 5 critical issues
            }

        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            return {"status": "error", "message": str(e)}

    def _run_linters(self) -> Dict:
        """Run Python and TS linters"""
        results = {"python": None, "typescript": None}

        # Python: Ruff
        try:
            result = subprocess.run(
                ["ruff", "check", str(self.project_dir / "backend")],
                capture_output=True,
                timeout=30
            )
            results["python"] = "pass" if result.returncode == 0 else "fail"
        except Exception as e:
            results["python"] = f"error: {e}"

        # TypeScript: ESLint
        try:
            result = subprocess.run(
                ["npx", "eslint", str(self.project_dir / "frontend")],
                capture_output=True,
                timeout=30
            )
            results["typescript"] = "pass" if result.returncode == 0 else "fail"
        except Exception as e:
            results["typescript"] = f"error: {e}"

        status = "pass" if all(r == "pass" for r in results.values()) else "fail"
        return {"status": status, "details": results}

    def _run_tests(self) -> Dict:
        """Run test suites"""
        results = {"backend": None, "frontend": None}

        # Backend pytest
        try:
            result = subprocess.run(
                ["pytest", str(self.project_dir / "backend/tests"), "-v"],
                capture_output=True,
                text=True,
                timeout=120
            )
            results["backend"] = {
                "status": "pass" if result.returncode == 0 else "fail",
                "output": result.stdout[-500:]  # Last 500 chars
            }
        except Exception as e:
            results["backend"] = {"status": "error", "message": str(e)}

        # Frontend Jest
        try:
            result = subprocess.run(
                ["npm", "test", "--prefix", str(self.project_dir / "frontend")],
                capture_output=True,
                timeout=120
            )
            results["frontend"] = {
                "status": "pass" if result.returncode == 0 else "fail"
            }
        except Exception as e:
            results["frontend"] = {"status": "error", "message": str(e)}

        status = "pass" if all(r.get("status") == "pass" for r in results.values()) else "fail"
        return {"status": status, "details": results}

    def _check_coverage(self) -> Dict:
        """Check test coverage"""
        try:
            result = subprocess.run(
                ["pytest", "--cov=app", "--cov-report=json", str(self.project_dir / "backend/tests")],
                capture_output=True,
                timeout=120
            )

            coverage_file = self.project_dir / "backend" / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                    total_coverage = data["totals"]["percent_covered"]

                    return {
                        "status": "pass" if total_coverage >= 80 else "fail",
                        "coverage": round(total_coverage, 2),
                        "threshold": 80
                    }

        except Exception as e:
            self.logger.error(f"Coverage check failed: {e}")

        return {"status": "error", "coverage": 0}

    def _validate_docker(self) -> Dict:
        """Validate Docker configuration"""
        compose_file = self.project_dir / "docker-compose.yml"

        if not compose_file.exists():
            return {"status": "skip", "reason": "No docker-compose.yml"}

        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                timeout=30
            )

            return {"status": "pass" if result.returncode == 0 else "fail"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def auto_fix(self) -> bool:
        """Attempt to auto-fix failures"""
        if not self.config.auto_fix_enabled:
            return False

        fixed = False

        # Fix linting issues
        if self.results.get("linting", {}).get("status") == "fail":
            self.logger.info("Auto-fixing linting issues...")

            # Ruff auto-fix
            subprocess.run(["ruff", "check", "--fix", str(self.project_dir / "backend")], timeout=30)

            # ESLint auto-fix
            subprocess.run(["npx", "eslint", "--fix", str(self.project_dir / "frontend")], timeout=30)

            fixed = True

        return fixed

# ============================================================================
# ORCHESTRATOR
# ============================================================================

class FullStackOrchestrator:
    """Complete workflow orchestration"""

    def __init__(self, config_path: Optional[Path] = None):
        # Load config
        if config_path and config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            self.config = SystemConfig(**config_data)
        else:
            self.config = SystemConfig(
                api_key=os.environ.get("MOONSHOT_API_KEY", ""),
                project_root=Path("generated_project")
            )

        # Initialize components
        self.logger = SystemLogger(self.config)
        self.cost_tracker = CostTracker(self.config.cost_limit_usd)

        self.logger.info("=" * 80)
        self.logger.info("Full-Stack AI Generation System v1.0 (2026)")
        self.logger.info("=" * 80)

    async def run(self, contract_path: Path) -> Path:
        """Execute complete generation workflow"""
        try:
            start_time = datetime.now()

            # Step 1: Parse contract
            self.logger.info("📋 Step 1: Parsing contract and generating types...")
            parser = ContractParser(contract_path, self.logger)
            parser.generate_pydantic_models()
            parser.generate_typescript_types()
            parser.generate_api_client()
            parser.generate_database_schema()

            # Step 2: Parallel generation
            self.logger.info("⚡ Step 2: Generating backend and frontend...")
            generator = ParallelGenerator(
                self.config,
                parser.contract,
                self.logger,
                self.cost_tracker
            )
            backend_code, frontend_code = await generator.generate_all()

            # Step 3: Parse to files
            self.logger.info("📁 Step 3: Creating project structure...")
            file_parser = FileParser(self.config.project_root, self.logger)
            backend_files = file_parser.parse_to_files(backend_code, "backend")
            frontend_files = file_parser.parse_to_files(frontend_code, "frontend")
            file_parser.generate_dependencies()

            # Step 4: Validate
            self.logger.info("🔍 Step 4: Running validation suite...")
            validator = AdvancedValidator(
                self.config.project_root,
                self.config,
                self.logger
            )
            results = validator.run_all_checks()

            # Step 5: Auto-fix if needed
            if results["overall"] == "fail":
                self.logger.info("🔧 Step 5: Attempting auto-fix...")
                if validator.auto_fix():
                    results = validator.run_all_checks()

            # Summary
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info("=" * 80)
            self.logger.info(f"✅ Generation complete in {duration:.1f}s")
            self.logger.info(f"📦 Project: {self.config.project_root}")
            self.logger.info(f"📄 Files: {len(backend_files)} backend, {len(frontend_files)} frontend")

            cost_report = self.cost_tracker.get_report()
            self.logger.info(f"💰 Cost: ${cost_report['total_cost']} (${cost_report['remaining_budget']} remaining)")

            for check, result in results.items():
                if check != "overall":
                    status = result.get("status", "unknown")
                    icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
                    self.logger.info(f"{icon} {check}: {status}")

            self.logger.info("=" * 80)

            return self.config.project_root

        except Exception as e:
            self.logger.error(f"❌ Generation failed: {e}")
            raise

# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Professional Full-Stack Generator")
    parser.add_argument("--contract", type=Path, default=Path("contract.yml"), help="Contract file")
    parser.add_argument("--config", type=Path, help="Config file (optional)")
    parser.add_argument("--output", type=Path, default=Path("generated_project"), help="Output directory")

    args = parser.parse_args()

    # Validate API key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("❌ Error: MOONSHOT_API_KEY environment variable required")
        print("Set it: export MOONSHOT_API_KEY='your-key-here'")
        return

    # Run orchestrator
    orchestrator = FullStackOrchestrator(args.config)
    orchestrator.config.project_root = args.output

    try:
        project_dir = await orchestrator.run(args.contract)
        print(f"\n🎉 Success! Project generated at: {project_dir}")
        print(f"\nNext steps:")
        print(f"  cd {project_dir}/backend && pip install -r requirements.txt && uvicorn app.main:app")
        print(f"  cd {project_dir}/frontend && npm install && npm run dev")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
