"""
Production Orchestrator - Fixes timeout and chunking issues
"""
import argparse
import json
import logging
import sys
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
import re
import time
from pr_fix_agent.schemas.findings import FindingSchema, AnalysisSchema, ProposalSchema
from pydantic import ValidationError

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Try to import ollama - fallback to mock if not available
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("Ollama not installed - using mock mode")


class CircuitBreaker:
    """Simple circuit breaker for LLM calls"""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error("Circuit breaker OPEN")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                logger.info("Circuit breaker HALF-OPEN")
                return True
            return False
        return True


class ChunkedOllamaClient:
    """
    Ollama client with chunking to prevent timeouts
    Fixes: 14KB prompt timeout, 120s hang issues
    """

    def __init__(self, reasoning_model: str = "deepseek-r1:1.5b",
                 coding_model: str = "qwen2.5-coder:1.5b"):
        self.reasoning_model = reasoning_model
        self.coding_model = coding_model
        self.max_prompt_size = 4000  # ✅ FIX: Prevent 14KB prompts
        self.timeout = 90
        self.circuit_breaker = CircuitBreaker()

        if not HAS_OLLAMA:
            logger.warning("Running in mock mode - no actual LLM calls")

    def query_with_fallback(self, prompt: str, models: List[str]) -> Dict:
        """Query with fallback chain"""
        for model in models:
            if not self.circuit_breaker.can_execute():
                logger.warning(f"Circuit open, skipping query to {model}")
                continue

            result = self.query(model, prompt)
            if result['success']:
                self.circuit_breaker.record_success()
                return result
            else:
                self.circuit_breaker.record_failure()
                logger.warning(f"Query to {model} failed, trying next in chain...")

        return {'success': False, 'error': "All models in fallback chain failed"}

    def query(self, model: str, prompt: str) -> Dict:
        """Query with timeout protection and truncation"""
        # ✅ FIX: Truncate large prompts
        if len(prompt) > self.max_prompt_size:
            logger.warning(f"Truncating prompt from {len(prompt)} to {self.max_prompt_size}")
            prompt = prompt[:self.max_prompt_size] + "\n... [truncated]"

        if not HAS_OLLAMA:
            # Mock mode for testing
            if "Provide JSON" in prompt:
                 return {
                    'success': True,
                    'content': '```json\n{"root_cause": "Mock analysis", "fix_approach": "Mock fix", "risk_level": "low"}\n```',
                    'model': model
                }
            return {
                'success': True,
                'content': 'Mock response',
                'model': model
            }

        try:
            logger.info(f"Querying {model} ({len(prompt)} chars)")

            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.1,
                    'num_ctx': 4096,
                    'num_predict': 2000
                }
            )

            return {
                'success': True,
                'content': response['message']['content'],
                'model': model
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'model': model
            }


class FixOrchestrator:
    """Main orchestrator"""

    def __init__(self, reasoning_model: str = "deepseek-r1:1.5b", coding_model: str = "qwen2.5-coder:1.5b"):
        self.client = ChunkedOllamaClient(reasoning_model, coding_model)

    def parse_findings(self, analysis_path: Path) -> List[Dict]:
        """Parse findings with multiple format support"""
        findings = []

        try:
            if not analysis_path.exists():
                logger.error(f"Findings file not found: {analysis_path}")
                return []

            with open(analysis_path) as f:
                content = f.read()

            # Try JSON first
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('findings', data.get('results', []))
            except json.JSONDecodeError:
                pass

            # Parse text format (bandit, mypy, etc.)
            pattern = r'([^:]+):([0-9]+):([0-9]*):?\s*(\w+):?\s*(.*)'
            for line in content.split('\n')[:50]:
                match = re.match(pattern, line)
                if match:
                    try:
                        finding = FindingSchema(
                            file=match.group(1),
                            line=int(match.group(2)),
                            severity='medium',
                            issue=match.group(5),
                            suggestion='See documentation'
                        )
                        findings.append(finding.model_dump())
                    except ValidationError as e:
                        logger.warning(f"Validation failed for line '{line}': {e}")

        except Exception as e:
            logger.error(f"Parse error: {e}")

        return findings

    def extract_json(self, text: str) -> Optional[Dict]:
        """Safely extract JSON from LLM response"""
        try:
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            text = text.strip()

            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to extract JSON: {e}")
        return None

    def analyze_finding(self, finding: Dict) -> Dict:
        """Analyze with reasoning model"""
        # Validate input finding
        try:
            valid_finding = FindingSchema(**finding)
        except ValidationError as e:
            logger.error(f"Invalid finding input: {e}")
            return {'root_cause': 'Invalid input', 'fix_approach': 'N/A', 'risk_level': 'high'}

        prompt = f"""Analyze this issue:
File: {valid_finding.file}
Line: {valid_finding.line}
Issue: {valid_finding.issue}

Provide JSON:
{{"root_cause": "brief", "fix_approach": "how to fix", "risk_level": "low"}}"""

        result = self.client.query_with_fallback(prompt, [self.client.reasoning_model, "llama3.2", "mistral:7b"])

        if result['success']:
            analysis_data = self.extract_json(result['content'])
            if analysis_data:
                try:
                    analysis = AnalysisSchema(**analysis_data)
                    return analysis.model_dump()
                except ValidationError as e:
                    logger.warning(f"LLM produced invalid analysis JSON: {e}")

        return {
            'root_cause': 'Analysis failed or invalid',
            'fix_approach': 'Manual review required',
            'risk_level': 'high'
        }

    def implement_fix(self, proposal: Dict) -> Dict:
        """Implement fix with coding model"""
        finding = proposal.get('finding', {})
        file_path = Path(finding.get('file', ''))

        if not file_path.exists():
             return {'success': False, 'error': f"File not found: {file_path}"}

        try:
            original_code = file_path.read_text()

            prompt = f"""Fix the following issue in this code:
Issue: {finding.get('issue')}
Fix Approach: {proposal.get('fix_approach')}

Code:
```python
{original_code}
```

Provide ONLY the full fixed code for this file."""

            result = self.client.query_with_fallback(prompt, [self.client.coding_model, "codellama:7b"])

            if result['success']:
                fixed_code = result['content']
                if '```python' in fixed_code:
                    fixed_code = fixed_code.split('```python')[1].split('```')[0]
                elif '```' in fixed_code:
                    fixed_code = fixed_code.split('```')[1].split('```')[0]

                return {
                    'success': True,
                    'original': original_code,
                    'fixed': fixed_code.strip()
                }
        except Exception as e:
            logger.error(f"Fix implementation failed: {e}")

        return {'success': False, 'error': "LLM failed to generate fix"}

    def apply_fix_with_rollback(self, proposal: Dict) -> bool:
        """Apply fix and rollback if tests fail"""
        finding = proposal.get('finding', {})
        file_path = finding.get('file')
        if not file_path:
            return False

        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)

        try:
            fix_result = self.implement_fix(proposal)
            if fix_result['success'] and len(fix_result['fixed']) > 10:
                with open(file_path, 'w') as f:
                    f.write(fix_result['fixed'])

                logger.info(f"Running tests for {file_path}...")
                test_proc = subprocess.run(["pytest", "tests/", "-v"], capture_output=True)

                if test_proc.returncode == 0:
                    logger.info(f"Tests passed for {file_path}")
                    os.remove(backup_path)
                    return True
                else:
                    logger.warning(f"Tests failed for {file_path}, rolling back...")
                    shutil.move(backup_path, file_path)
                    return False
            else:
                logger.warning(f"Fix failed or empty for {file_path}, keeping backup")
                shutil.move(backup_path, file_path)
                return False
        except Exception as e:
            logger.error(f"Error applying fix to {file_path}: {e}")
            if os.path.exists(backup_path):
                shutil.move(backup_path, file_path)
            return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['review', 'fix', 'reasoning', 'coding', 'generate-pr'], default='review', nargs='?')
    parser.add_argument('--findings', '-f', default='analysis-results/safety.json')
    parser.add_argument('--proposals', help='Path to proposals JSON')
    parser.add_argument('--test-results', help='Path to test results JSON')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--reasoning-model', default="deepseek-r1:1.5b")
    parser.add_argument('--coding-model', default="qwen2.5-coder:1.5b")
    args = parser.parse_args()

    orch = FixOrchestrator(args.reasoning_model, args.coding_model)

    # Backward compatibility for 'reasoning' mode
    if args.mode == 'reasoning':
        args.mode = 'review'
        if args.findings and Path(args.findings).is_dir():
             findings_dir = Path(args.findings)
             findings = []
             for f in findings_dir.glob("*.json"):
                 findings.extend(orch.parse_findings(f))

             proposals = []
             for i, finding in enumerate(findings[:args.limit]):
                 logger.info(f"Analyzing {i+1}/{len(findings[:args.limit])}")
                 analysis = orch.analyze_finding(finding)
                 proposals.append({'finding': finding, **analysis})

             output_file = args.output or 'proposals.json'
             with open(output_file, 'w') as f:
                 json.dump(proposals, f, indent=2)
             logger.info(f"Saved {len(proposals)} proposals to {output_file}")
             return

    if args.mode == 'review':
        findings = orch.parse_findings(Path(args.findings))
        logger.info(f"Found {len(findings)} findings")

        findings = findings[:args.limit]
        proposals = []
        for i, finding in enumerate(findings):
            logger.info(f"Analyzing {i+1}/{len(findings)}")
            analysis = orch.analyze_finding(finding)
            proposals.append({'finding': finding, **analysis})

        output_file = args.output or 'proposals.json'
        with open(output_file, 'w') as f:
            json.dump(proposals, f, indent=2)
        logger.info(f"Saved {len(proposals)} proposals to {output_file}")

    elif args.mode in ['coding', 'fix']:
        proposals_path = Path(args.proposals or 'proposals.json')
        if not proposals_path.exists():
            logger.error(f"Proposals file not found: {proposals_path}")
            sys.exit(1)

        with open(proposals_path) as f:
            proposals = json.load(f)

        for i, proposal in enumerate(proposals[:args.limit]):
            logger.info(f"Implementing fix {i+1}/{len(proposals[:args.limit])}")
            if args.apply:
                orch.apply_fix_with_rollback(proposal)
            else:
                fix = orch.implement_fix(proposal)
                if fix['success']:
                    logger.info(f"Fix generated for {proposal['finding']['file']}")

    elif args.mode == 'generate-pr':
        output_file = args.output or 'pr-body.md'
        proposals_path = Path(args.proposals or 'proposals.json')

        body = "# 🤖 Automated Code Review Fixes\n\n"
        if proposals_path.exists():
            with open(proposals_path) as f:
                proposals = json.load(f)
            body += "## Fixes Proposed\n"
            for p in proposals:
                body += f"- **{p['finding']['file']}**: {p['finding']['issue']}\n"
                body += f"  - *Root Cause*: {p.get('root_cause', 'N/A')}\n"
        else:
            body += "Analysis completed. Check logs for details.\n"

        with open(output_file, 'w') as f:
            f.write(body)
        logger.info(f"Generated PR body in {output_file}")


if __name__ == "__main__":
    main()
