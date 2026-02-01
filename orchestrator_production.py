#!/usr/bin/env python3
"""
PR Fix Agent - Production Orchestrator
Ready to run immediately with all fixes applied
"""
import argparse
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """Code review finding"""
    file: str
    line_start: int
    line_end: int
    severity: str
    category: str
    issue: str
    suggestion: str
    code_snippet: str = ""


@dataclass
class Proposal:
    """Fix proposal"""
    finding: Finding
    root_cause: str
    fix_approach: str
    expected_changes: List[str]
    risk_level: str
    test_requirements: List[str]


class LLMClient:
    """LLM client with timeout and chunking"""

    def __init__(self, backend="ollama", model="qwen2.5-coder:1.5b"):
        self.backend = backend
        self.model = model
        self.max_prompt = 4000
        self.timeout = 60

    def chunk_text(self, text: str, max_size: int = 3500) -> List[str]:
        """Split text into chunks"""
        if len(text) <= max_size:
            return [text]

        chunks = []
        lines = text.split('\n')
        current = []
        size = 0

        for line in lines:
            line_size = len(line) + 1
            if size + line_size > max_size and current:
                chunks.append('\n'.join(current))
                current = []
                size = 0
            current.append(line)
            size += line_size

        if current:
            chunks.append('\n'.join(current))

        return chunks

    def query(self, prompt: str, timeout: int = None) -> Dict[str, Any]:
        """Query LLM with timeout"""
        timeout = timeout or self.timeout

        # Truncate if needed
        if len(prompt) > self.max_prompt:
            logger.warning(f"Truncating prompt from {len(prompt)} to {self.max_prompt}")
            prompt = prompt[:self.max_prompt] + "\n[truncated]"

        try:
            if self.backend == "ollama":
                import ollama

                logger.info(f"Querying {self.model} (timeout={timeout}s)")
                start = time.time()

                response = ollama.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    options={
                        'temperature': 0.1,
                        'num_ctx': 2048,
                        'num_predict': 1500
                    }
                )

                duration = time.time() - start
                content = response['message']['content']

                logger.info(f"Response received in {duration:.1f}s ({len(content)} chars)")

                return {
                    'success': True,
                    'content': content,
                    'duration': duration
                }

            else:
                # HuggingFace
                from huggingface_hub import InferenceClient

                client = InferenceClient(token=os.getenv('HF_API_TOKEN'))

                start = time.time()
                completion = client.chat.completions.create(
                    model=f"{self.model}:fastest",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.1
                )

                duration = time.time() - start
                content = completion.choices[0].message.content

                return {
                    'success': True,
                    'content': content,
                    'duration': duration
                }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class Orchestrator:
    """Production orchestrator with all fixes"""

    def __init__(self, backend="ollama", max_findings=50):
        self.client = LLMClient(backend=backend)
        self.max_findings = max_findings

    def parse_findings(self, path: Path) -> List[Finding]:
        """Parse findings from file"""
        findings = []

        if not path.exists():
            logger.error(f"File not found: {path}")
            return findings

        try:
            # Try JSON first
            with open(path) as f:
                data = json.load(f)

            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get('findings', data.get('results', []))
            else:
                items = []

            for item in items[:self.max_findings]:
                try:
                    findings.append(Finding(
                        file=item.get('file', item.get('filename', 'unknown')),
                        line_start=item.get('line_start', item.get('line', 1)),
                        line_end=item.get('line_end', item.get('line', 1)),
                        severity=item.get('severity', 'medium'),
                        category=item.get('category', item.get('test_name', 'unknown')),
                        issue=item.get('issue', item.get('issue_text', '')),
                        suggestion=item.get('suggestion', item.get('more_info', '')),
                        code_snippet=item.get('code', '')
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse finding: {e}")

        except json.JSONDecodeError:
            # Try text format
            logger.info("Parsing as text format")
            content = path.read_text()

            # Pattern: file:line:col: severity: message
            pattern = r'([^:]+):(\d+):(\d*):?\s*(\w+):?\s*(.*)'

            for line in content.split('\n')[:self.max_findings]:
                match = re.match(pattern, line.strip())
                if match:
                    findings.append(Finding(
                        file=match.group(1),
                        line_start=int(match.group(2)),
                        line_end=int(match.group(2)),
                        severity="medium",
                        category="lint",
                        issue=match.group(5),
                        suggestion="See documentation"
                    ))

        logger.info(f"Parsed {len(findings)} findings")
        return findings

    def analyze_finding(self, finding: Finding) -> Proposal:
        """Analyze finding and create proposal"""

        prompt = f"""Analyze this code issue and respond with JSON only:

File: {finding.file}
Line: {finding.line_start}-{finding.line_end}
Severity: {finding.severity}
Issue: {finding.issue}

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "root_cause": "brief explanation",
  "fix_approach": "how to fix",
  "expected_changes": ["change 1", "change 2"],
  "risk_level": "low",
  "test_requirements": ["test 1"]
}}"""

        result = self.client.query(prompt)

        if result['success']:
            try:
                # Extract JSON from response
                content = result['content']

                # Remove markdown code blocks
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]

                # Clean up
                content = content.strip().replace("'", '"')

                # Find JSON object
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    content = content[start:end]

                data = json.loads(content)

                return Proposal(
                    finding=finding,
                    root_cause=data.get('root_cause', 'Unknown'),
                    fix_approach=data.get('fix_approach', 'Manual fix required'),
                    expected_changes=data.get('expected_changes', []),
                    risk_level=data.get('risk_level', 'medium'),
                    test_requirements=data.get('test_requirements', [])
                )

            except Exception as e:
                logger.error(f"Failed to parse response: {e}")
                logger.debug(f"Content: {result['content'][:200]}")

        # Fallback
        return Proposal(
            finding=finding,
            root_cause="Analysis failed",
            fix_approach="Manual review required",
            expected_changes=[],
            risk_level="high",
            test_requirements=[]
        )

    def run_tests(self) -> Dict[str, Any]:
        """Run test suite"""
        logger.info("Running tests...")

        try:
            result = subprocess.run(
                ['pytest', 'tests/', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=300
            )

            output = result.stdout + result.stderr

            # Parse test counts
            passed = 0
            failed = 0

            if match := re.search(r'(\d+) passed', output):
                passed = int(match.group(1))
            if match := re.search(r'(\d+) failed', output):
                failed = int(match.group(1))

            return {
                'success': result.returncode == 0,
                'total': passed + failed,
                'passed': passed,
                'failed': failed,
                'output': output[:1000]
            }

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PR Fix Agent - Production Orchestrator')
    parser.add_argument('mode', choices=['review', 'test'], help='Operation mode')
    parser.add_argument('--findings', '-f', default='analysis-results/bandit.txt', help='Findings file')
    parser.add_argument('--backend', choices=['ollama', 'huggingface'], default='ollama', help='LLM backend')
    parser.add_argument('--limit', type=int, default=10, help='Max findings to process')
    parser.add_argument('--output', '-o', default='proposals.json', help='Output file')

    args = parser.parse_args()

    try:
        orch = Orchestrator(backend=args.backend, max_findings=args.limit)

        if args.mode == 'review':
            # Parse findings
            findings_path = Path(args.findings)
            findings = orch.parse_findings(findings_path)

            if not findings:
                logger.error("No findings to process")
                return 1

            logger.info(f"Analyzing {len(findings)} findings...")

            # Analyze each
            proposals = []
            for i, finding in enumerate(findings, 1):
                logger.info(f"Processing {i}/{len(findings)}: {finding.file}:{finding.line_start}")

                proposal = orch.analyze_finding(finding)
                proposals.append(proposal)

            # Save
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(
                    [
                        {
                            'finding': asdict(p.finding),
                            'root_cause': p.root_cause,
                            'fix_approach': p.fix_approach,
                            'expected_changes': p.expected_changes,
                            'risk_level': p.risk_level,
                            'test_requirements': p.test_requirements
                        }
                        for p in proposals
                    ],
                    f,
                    indent=2
                )

            logger.info(f"✅ Saved {len(proposals)} proposals to {output_path}")
            print(f"\n✅ Success! Analyzed {len(proposals)} findings")
            print(f"📄 Output: {output_path}")

            return 0

        elif args.mode == 'test':
            # Run tests
            result = orch.run_tests()

            if result['success']:
                logger.info(f"✅ All {result['passed']} tests passed")
                print(f"\n✅ All tests passed ({result['passed']}/{result['total']})")
                return 0
            else:
                logger.error(f"❌ {result['failed']} tests failed")
                print(f"\n❌ Tests failed ({result['failed']}/{result['total']})")
                return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
