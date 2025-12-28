"""
Vaal AI Empire - Rainmaker Orchestrator
Full Production Implementation
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Available AI tools in the empire"""
    KIMI_LINEAR = "kimi"
    GEMINI_PRO = "gemini"
    GROK = "grok"
    COHERE = "cohere"
    PERPLEXITY = "perplexity"
    ATLAS_TV = "atlas"
    LINEAR = "linear"
    VLLM = "vllm"


@dataclass
class DirectiveResult:
    """Result from executing a directive"""
    success: bool
    tool: str
    response: Any
    execution_time: float
    error: Optional[str] = None


class ConfigManager:
    """Manages API keys and configuration"""

    def __init__(self, config_file: str = ".env"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment or .env file"""
        config = {}

        # Try to load from .env file
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')

        # Override with environment variables
        config.update({
            'VLLM_ENDPOINT': os.getenv('VLLM_ENDPOINT', 'http://localhost:8000'),
            'QDRANT_HOST': os.getenv('QDRANT_HOST', 'localhost'),
            'QDRANT_PORT': os.getenv('QDRANT_PORT', '6333'),
            'PROMETHEUS_URL': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
            'GROK_API_KEY': os.getenv('GROK_API_KEY', ''),
            'COHERE_API_KEY': os.getenv('COHERE_API_KEY', ''),
            'PERPLEXITY_API_KEY': os.getenv('PERPLEXITY_API_KEY', ''),
            'LINEAR_API_KEY': os.getenv('LINEAR_API_KEY', ''),
            'LINEAR_TEAM_ID': os.getenv('LINEAR_TEAM_ID', ''),
            'ATLAS_API_KEY': os.getenv('ATLAS_API_KEY', ''),
        })

        return config

    def get(self, key: str, default: str = '') -> str:
        """Get configuration value"""
        return self.config.get(key, default)

    def validate(self) -> List[str]:
        """Validate that required keys are present"""
        required_keys = [
            'VLLM_ENDPOINT', 'GEMINI_API_KEY', 'GROK_API_KEY',
            'COHERE_API_KEY', 'PERPLEXITY_API_KEY', 'LINEAR_API_KEY',
            'LINEAR_TEAM_ID', 'ATLAS_API_KEY'
        ]
        missing = [key for key in required_keys if not self.config.get(key)]
        return missing


class DirectiveParser:
    """Parses natural language directives into structured commands"""

    KEYWORDS = {
        'analyze': ToolType.KIMI_LINEAR,
        'history': ToolType.KIMI_LINEAR,
        'roadmap': ToolType.KIMI_LINEAR,
        'translate': ToolType.GEMINI_PRO,
        'vision': ToolType.GEMINI_PRO,
        'image': ToolType.GEMINI_PRO,
        'photo': ToolType.GEMINI_PRO,
        'search': ToolType.GROK,
        'news': ToolType.GROK,
        'trending': ToolType.GROK,
        'filter': ToolType.COHERE,
        'classify': ToolType.COHERE,
        'rerank': ToolType.COHERE,
        'patent': ToolType.PERPLEXITY,
        'legal': ToolType.PERPLEXITY,
        'infringement': ToolType.PERPLEXITY,
        'ad': ToolType.ATLAS_TV,
        'broadcast': ToolType.ATLAS_TV,
        'task': ToolType.LINEAR,
        'ticket': ToolType.LINEAR,
        'issue': ToolType.LINEAR,
    }

    @classmethod
    def parse(cls, directive: str) -> tuple[ToolType, str]:
        """
        Parse a directive into tool type and cleaned prompt

        Args:
            directive: Natural language directive

        Returns:
            Tuple of (ToolType, cleaned_prompt)
        """
        directive_lower = directive.lower()

        # Check for explicit tool specification
        if directive_lower.startswith('kimi'):
            return ToolType.KIMI_LINEAR, directive[4:].strip().strip('"')
        elif directive_lower.startswith('gemini'):
            return ToolType.GEMINI_PRO, directive[6:].strip().strip('"')
        elif directive_lower.startswith('grok'):
            return ToolType.GROK, directive[4:].strip().strip('"')
        elif directive_lower.startswith('cohere'):
            return ToolType.COHERE, directive[6:].strip().strip('"')
        elif directive_lower.startswith('perplexity'):
            return ToolType.PERPLEXITY, directive[10:].strip().strip('"')
        elif directive_lower.startswith('atlas'):
            return ToolType.ATLAS_TV, directive[5:].strip().strip('"')
        elif directive_lower.startswith('linear'):
            return ToolType.LINEAR, directive[6:].strip().strip('"')

        # Infer from keywords
        for keyword, tool in cls.KEYWORDS.items():
            if keyword in directive_lower:
                return tool, directive

        # Default to Kimi for analysis tasks
        return ToolType.KIMI_LINEAR, directive


class ToolExecutor:
    """Executes commands on specific AI tools"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.client = httpx.AsyncClient(timeout=120.0)

    async def execute(self, tool: ToolType, prompt: str) -> DirectiveResult:
        """Execute a command on the specified tool"""
        start_time = datetime.now()

        try:
            if tool == ToolType.KIMI_LINEAR:
                result = await self._execute_kimi(prompt)
            elif tool == ToolType.GEMINI_PRO:
                result = await self._execute_gemini(prompt)
            elif tool == ToolType.GROK:
                result = await self._execute_grok(prompt)
            elif tool == ToolType.COHERE:
                result = await self._execute_cohere(prompt)
            elif tool == ToolType.PERPLEXITY:
                result = await self._execute_perplexity(prompt)
            elif tool == ToolType.ATLAS_TV:
                result = await self._execute_atlas(prompt)
            elif tool == ToolType.LINEAR:
                result = await self._execute_linear(prompt)
            else:
                raise ValueError(f"Unknown tool: {tool}")

            execution_time = (datetime.now() - start_time).total_seconds()

            return DirectiveResult(
                success=True,
                tool=tool.value,
                response=result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error executing {tool.value}: {str(e)}")

            return DirectiveResult(
                success=False,
                tool=tool.value,
                response=None,
                execution_time=execution_time,
                error=str(e)
            )

    async def _execute_kimi(self, prompt: str) -> Dict:
        """Execute on Kimi Linear (vLLM)"""
        endpoint = self.config.get('VLLM_ENDPOINT')

        response = await self.client.post(
            f"{endpoint}/v1/completions",
            json={
                "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
                "prompt": prompt,
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_gemini(self, prompt: str) -> Dict:
        """Execute on Gemini 3 Pro"""
        api_key = self.config.get('GEMINI_API_KEY')

        response = await self.client.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}",
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                }
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_grok(self, prompt: str) -> Dict:
        """Execute on Grok 4.1"""
        api_key = self.config.get('GROK_API_KEY')

        response = await self.client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "grok-beta",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_cohere(self, prompt: str) -> Dict:
        """Execute on Cohere"""
        api_key = self.config.get('COHERE_API_KEY')

        response = await self.client.post(
            "https://api.cohere.ai/v1/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "command",
                "prompt": prompt,
                "max_tokens": 1024,
                "temperature": 0.7,
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_perplexity(self, prompt: str) -> Dict:
        """Execute on Perplexity"""
        api_key = self.config.get('PERPLEXITY_API_KEY')

        response = await self.client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "pplx-7b-online",
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_atlas(self, prompt: str) -> Dict:
        """Execute on Atlas TV Ad AI"""
        api_key = self.config.get('ATLAS_API_KEY')

        # This would be your custom Atlas API endpoint
        response = await self.client.post(
            "https://atlas.vaal-ai-empire.com/api/v1/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "prompt": prompt,
                "ad_type": "tv",
                "duration": 30,
            }
        )
        response.raise_for_status()
        return response.json()

    async def _execute_linear(self, prompt: str) -> Dict:
        """Execute on Linear (create/update tasks)"""
        api_key = self.config.get('LINEAR_API_KEY')

        # GraphQL mutation for creating an issue
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              title
              url
            }
          }
        }
        """

        response = await self.client.post(
            "https://api.linear.app/graphql",
            headers={"Authorization": api_key},
            json={
                "query": query,
                "variables": {
                    "input": {
                        "title": prompt[:100],
                        "description": prompt,
                        "teamId": self.config.get('LINEAR_TEAM_ID'),
                    }
                }
            }
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class RainmakerOrchestrator:
    """Main orchestrator for the Vaal AI Empire"""

    def __init__(self, config_file: str = ".env"):
        self.config = ConfigManager(config_file)
        self.executor = ToolExecutor(self.config)
        self.parser = DirectiveParser()

        # Validate configuration
        missing = self.config.validate()
        if missing:
            logger.warning(f"Missing configuration keys: {', '.join(missing)}")

    async def execute_directive(self, directive: str) -> DirectiveResult:
        """
        Execute a natural language directive

        Args:
            directive: Natural language command (e.g., "Analyze project history")

        Returns:
            DirectiveResult with execution details
        """
        logger.info(f"Executing directive: {directive}")

        # Parse directive to determine tool and clean prompt
        tool, prompt = self.parser.parse(directive)
        logger.info(f"Routing to {tool.value}: {prompt[:100]}...")

        # Execute on the appropriate tool
        result = await self.executor.execute(tool, prompt)

        if result.success:
            logger.info(f"✓ Completed in {result.execution_time:.2f}s")
        else:
            logger.error(f"✗ Failed: {result.error}")

        return result

    async def batch_execute(self, directives: List[str]) -> List[DirectiveResult]:
        """Execute multiple directives concurrently"""
        tasks = [self.execute_directive(d) for d in directives]
        return await asyncio.gather(*tasks)

    async def close(self):
        """Cleanup resources"""
        await self.executor.close()


# CLI Interface
async def main():
    """Main CLI entry point"""
    import sys

    orchestrator = RainmakerOrchestrator()

    if len(sys.argv) > 1:
        # Execute directive from command line
        directive = ' '.join(sys.argv[1:])
        result = await orchestrator.execute_directive(directive)

        print(f"\n{'='*60}")
        print(f"Tool: {result.tool}")
        print(f"Status: {'✓ Success' if result.success else '✗ Failed'}")
        print(f"Time: {result.execution_time:.2f}s")
        print(f"{'='*60}\n")

        if result.success:
            print(json.dumps(result.response, indent=2))
        else:
            print(f"Error: {result.error}")
    else:
        # Interactive mode
        print("\n🚀 Vaal AI Empire - Rainmaker Orchestrator")
        print("Built in the Vaal. Built for Africa. Built to dominate.\n")

        while True:
            try:
                directive = input("💫 Enter directive (or 'quit' to exit): ").strip()

                if directive.lower() in ['quit', 'exit', 'q']:
                    break

                if not directive:
                    continue

                result = await orchestrator.execute_directive(directive)

                print(f"\n{'─'*60}")
                print(f"✓ Completed in {result.execution_time:.2f}s via {result.tool}")

                if result.success:
                    response_str = json.dumps(result.response, indent=2)
                    # Show first 500 chars of response
                    if len(response_str) > 500:
                        print(response_str[:500] + "...\n[truncated]")
                    else:
                        print(response_str)
                else:
                    print(f"✗ Error: {result.error}")
                print(f"{'─'*60}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}\n")

    await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())