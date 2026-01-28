#!/usr/bin/env python3
"""
Agent-Driven Continuous Improvement System
Automatically identifies and implements improvements based on evaluation results
"""

import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests


@dataclass
class Improvement:
    """Represents a suggested improvement"""
    id: str
    category: str  # security, performance, quality, usability
    priority: str  # critical, high, medium, low
    title: str
    description: str
    affected_files: List[str]
    implementation: str  # Code or instructions
    test_cases: List[str]
    estimated_impact: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class AgentImprovementGenerator:
    """Uses agents to generate improvement suggestions"""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "codellama"):
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/generate"
        self.moonshot_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        self.cohere_key = os.getenv("COHER_API_KEY") or os.getenv("COHERE_API_KEY")

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        """Query AI Model with Fallback"""
        # Same fallback logic as evaluation_system.py
        errors = []
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=1)
            if response.status_code == 200:
                response = requests.post(
                    self.api_url,
                    json={"model": self.model, "prompt": prompt, "stream": False, "temperature": temperature},
                    timeout=120
                )
                return response.json()["response"]
        except Exception as e:
            errors.append(f"Ollama Error: {e}")

        if self.moonshot_key:
            try:
                response = requests.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.moonshot_key}", "Content-Type": "application/json"},
                    json={"model": os.getenv("KIMI_MODEL", "kimi-latest"), "messages": [{"role": "user", "content": prompt}], "temperature": temperature},
                    timeout=120
                )
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                errors.append(f"Moonshot Error: {e}")

        if self.cohere_key:
            try:
                response = requests.post(
                    "https://api.cohere.com/v1/generate",
                    headers={"Authorization": f"Bearer {self.cohere_key}", "Content-Type": "application/json"},
                    json={"model": "command", "prompt": prompt, "temperature": temperature, "max_tokens": 1000},
                    timeout=120
                )
                return response.json()["generations"][0]["text"]
            except Exception as e:
                errors.append(f"Cohere Error: {e}")

        return f"Error: No AI provider reachable. Details: {'; '.join(errors)}"

    def analyze_failures(self, evaluation_results: List[Dict]) -> List[Improvement]:
        """Analyze failed tests and generate improvements"""
        print("\n🔍 Analyzing Failures...")

        # Group failures by category
        failures = [r for r in evaluation_results if not r.get("passed", False)]

        if not failures:
            print("  ✅ No failures to analyze!")
            return []

        print(f"  Found {len(failures)} failed tests")

        improvements = []

        # Analyze each failure
        for failure in failures[:5]:  # Limit to top 5 for efficiency
            improvement = self._generate_improvement_for_failure(failure)
            if improvement:
                improvements.append(improvement)

        return improvements

    def _generate_improvement_for_failure(self, failure: Dict) -> Optional[Improvement]:
        """Generate improvement suggestion for a specific failure"""
        test_name = failure.get("test_name", "Unknown")
        message = failure.get("message", "")
        details = failure.get("details", {})
        level = failure.get("level", "unknown")

        prompt = f"""Analyze this test failure and suggest a specific, actionable improvement:

Test: {test_name}
Level: {level}
Message: {message}
Details: {json.dumps(details, indent=2)}

Provide your response in JSON format:
{{
    "category": "security|performance|quality|usability",
    "priority": "critical|high|medium|low",
    "title": "Brief title",
    "description": "Detailed description",
    "affected_files": ["file1.py"],
    "implementation": "Specific code changes",
    "test_cases": ["Test case 1"],
    "estimated_impact": 0.0-1.0,
    "confidence": 0.0-1.0
}}
"""

        response = self.query(prompt, temperature=0.2)

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                return Improvement(
                    id=f"imp_{test_name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}",
                    category=data.get("category", "quality"),
                    priority=data.get("priority", "medium"),
                    title=data.get("title", f"Fix {test_name}"),
                    description=data.get("description", ""),
                    affected_files=data.get("affected_files", []),
                    implementation=data.get("implementation", ""),
                    test_cases=data.get("test_cases", []),
                    estimated_impact=data.get("estimated_impact", 0.5),
                    confidence=data.get("confidence", 0.5)
                )
        except:
            pass

        return None


class ContinuousImprovementEngine:
    """Orchestrates continuous improvement process"""

    def __init__(self, repo_path: Path, improvement_generator: AgentImprovementGenerator):
        self.repo_path = Path(repo_path)
        self.generator = improvement_generator
        self.improvements_log = self.repo_path / ".improvements_log.json"

    def run_improvement_cycle(self, evaluation_results: List[Dict]) -> Dict:
        """Run a complete improvement cycle"""
        print("\n" + "="*70)
        print("🔄 CONTINUOUS IMPROVEMENT CYCLE")
        print("="*70)

        # Step 1: Analyze failures
        failure_improvements = self.generator.analyze_failures(evaluation_results)

        # Step 2: Combine and prioritize
        all_improvements = failure_improvements
        prioritized = sorted(all_improvements, key=lambda x: (x.priority, x.estimated_impact), reverse=True)

        # Step 3: Log improvements
        self._log_improvements(prioritized)

        return {
            "total_improvements": len(prioritized),
            "improvements": prioritized
        }

    def _log_improvements(self, improvements: List[Improvement]):
        """Log improvements to file"""
        try:
            log = {"cycles": []}
            if self.improvements_log.exists():
                with open(self.improvements_log, 'r') as f:
                    log = json.load(f)

            log["cycles"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "improvements": [asdict(imp) for imp in improvements]
            })

            with open(self.improvements_log, 'w') as f:
                json.dump(log, f, indent=2)
        except:
            pass

    def generate_improvement_report(self, cycle_results: Dict, output_path: Optional[Path] = None) -> str:
        """Generate a detailed improvement report"""
        report = f"# Continuous Improvement Report\nGenerated: {datetime.utcnow().isoformat()}\n\n"
        report += f"- **Total Improvements Identified:** {cycle_results['total_improvements']}\n\n"

        for imp in cycle_results['improvements']:
            report += f"### {imp.title} ({imp.priority.upper()})\n"
            report += f"- **Category:** {imp.category}\n"
            report += f"- **Affected Files:** {', '.join(imp.affected_files)}\n"
            report += f"- **Implementation:**\n```\n{imp.implementation}\n```\n\n"

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Continuous Improvement System")
    parser.add_argument("evaluation_results", help="Path to evaluation results JSON")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--model", default="codellama", help="Ollama model")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--report", help="Path to save improvement report")
    args = parser.parse_args()

    try:
        with open(args.evaluation_results, 'r') as f:
            eval_data = json.load(f)
        results = eval_data.get("results", [])
    except:
        results = []

    generator = AgentImprovementGenerator(ollama_url=args.ollama_url, model=args.model)
    engine = ContinuousImprovementEngine(Path(args.repo_path), generator)
    cycle_results = engine.run_improvement_cycle(results)

    if args.report:
        engine.generate_improvement_report(cycle_results, Path(args.report))
        print(f"Report saved to {args.report}")


if __name__ == "__main__":
    main()
