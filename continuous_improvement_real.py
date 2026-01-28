#!/usr/bin/env python3
"""
REAL Continuous Improvement System
Actually analyzes code and generates actionable improvements
"""

import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class CodeIssue:
    """Real code issue found"""
    file: str
    line: int
    severity: str  # critical, high, medium, low
    category: str  # security, performance, quality, style
    issue: str
    suggestion: str
    code_snippet: str


@dataclass
class Improvement:
    """Real improvement suggestion"""
    id: str
    priority: str
    category: str
    title: str
    description: str
    affected_files: List[str]
    impact_score: float  # 0-1
    effort_score: float  # 0-1 (lower is easier)
    implementation: str


class StaticAnalyzer:
    """Real static code analysis"""

    def analyze_python_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze Python file for issues"""
        issues = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return [CodeIssue(
                    file=str(file_path),
                    line=e.lineno or 0,
                    severity="critical",
                    category="quality",
                    issue="Syntax error",
                    suggestion="Fix syntax error",
                    code_snippet=lines[e.lineno-1] if e.lineno else ""
                )]

            # Check for common issues
            issues.extend(self._check_security(content, lines, file_path))
            issues.extend(self._check_performance(tree, lines, file_path))
            issues.extend(self._check_code_quality(tree, lines, file_path))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return issues

    def _check_security(self, content: str, lines: List[str], file_path: Path) -> List[CodeIssue]:
        """Check for security issues"""
        issues = []

        # Check for eval/exec
        for i, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line):
                issues.append(CodeIssue(
                    file=str(file_path),
                    line=i,
                    severity="critical",
                    category="security",
                    issue="Use of eval() is dangerous",
                    suggestion="Use ast.literal_eval() or safer alternatives",
                    code_snippet=line.strip()
                ))

            if re.search(r'\bexec\s*\(', line):
                issues.append(CodeIssue(
                    file=str(file_path),
                    line=i,
                    severity="critical",
                    category="security",
                    issue="Use of exec() is dangerous",
                    suggestion="Refactor to avoid dynamic code execution",
                    code_snippet=line.strip()
                ))

            # Check for shell=True
            if 'shell=True' in line:
                issues.append(CodeIssue(
                    file=str(file_path),
                    line=i,
                    severity="high",
                    category="security",
                    issue="subprocess with shell=True is dangerous",
                    suggestion="Use shell=False and pass args as list",
                    code_snippet=line.strip()
                ))

            # Check for hardcoded secrets
            if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    file=str(file_path),
                    line=i,
                    severity="high",
                    category="security",
                    issue="Possible hardcoded secret",
                    suggestion="Use environment variables or secret management",
                    code_snippet=line.strip()[:50] + "..."
                ))

        return issues

    def _check_performance(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeIssue]:
        """Check for performance issues"""
        issues = []

        class PerformanceVisitor(ast.NodeVisitor):
            def __init__(self, issues_list, lines_list, file_path_obj):
                self.issues = issues_list
                self.lines = lines_list
                self.file_path = file_path_obj

            def visit_For(self, node):
                # Check for list concatenation in loop
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                        # Look for list += in body
                        for stmt in ast.walk(node):
                            if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                                if isinstance(stmt.target, ast.Name):
                                    self.issues.append(CodeIssue(
                                        file=str(self.file_path),
                                        line=node.lineno,
                                        severity="medium",
                                        category="performance",
                                        issue="List concatenation in loop is slow",
                                        suggestion="Use list comprehension or append()",
                                        code_snippet=self.lines[node.lineno-1].strip() if node.lineno <= len(self.lines) else ""
                                    ))

                self.generic_visit(node)

            def visit_Call(self, node):
                # Check for inefficient string formatting
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'format' and isinstance(node.func.value, ast.Str):
                        # Old style string formatting
                        pass  # Could suggest f-strings

                self.generic_visit(node)

        visitor = PerformanceVisitor(issues, lines, file_path)
        visitor.visit(tree)

        return issues

    def _check_code_quality(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeIssue]:
        """Check code quality issues"""
        issues = []

        class QualityVisitor(ast.NodeVisitor):
            def __init__(self, issues_list, lines_list, file_path_obj):
                self.issues = issues_list
                self.lines = lines_list
                self.file_path = file_path_obj

            def visit_FunctionDef(self, node):
                # Check for missing docstring
                docstring = ast.get_docstring(node)
                if not docstring and not node.name.startswith('_'):
                    self.issues.append(CodeIssue(
                        file=str(self.file_path),
                        line=node.lineno,
                        severity="low",
                        category="quality",
                        issue=f"Function '{node.name}' missing docstring",
                        suggestion="Add docstring to explain function purpose",
                        code_snippet=self.lines[node.lineno-1].strip() if node.lineno <= len(self.lines) else ""
                    ))

                # Check function length
                if len(node.body) > 50:
                    self.issues.append(CodeIssue(
                        file=str(self.file_path),
                        line=node.lineno,
                        severity="medium",
                        category="quality",
                        issue=f"Function '{node.name}' is too long ({len(node.body)} lines)",
                        suggestion="Consider breaking into smaller functions",
                        code_snippet=self.lines[node.lineno-1].strip() if node.lineno <= len(self.lines) else ""
                    ))

                # Check parameter count
                if len(node.args.args) > 5:
                    self.issues.append(CodeIssue(
                        file=str(self.file_path),
                        line=node.lineno,
                        severity="low",
                        category="quality",
                        issue=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                        suggestion="Consider using a config object or kwargs",
                        code_snippet=self.lines[node.lineno-1].strip() if node.lineno <= len(self.lines) else ""
                    ))

                self.generic_visit(node)

            def visit_Try(self, node):
                # Check for bare except
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues.append(CodeIssue(
                            file=str(self.file_path),
                            line=handler.lineno,
                            severity="medium",
                            category="quality",
                            issue="Bare except clause catches all exceptions",
                            suggestion="Catch specific exceptions",
                            code_snippet=self.lines[handler.lineno-1].strip() if handler.lineno <= len(self.lines) else ""
                        ))

                self.generic_visit(node)

        visitor = QualityVisitor(issues, lines, file_path)
        visitor.visit(tree)

        return issues


class ImprovementGenerator:
    """Generate improvements using Ollama"""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "codellama"):
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/generate"

    def query(self, prompt: str) -> str:
        """Query Ollama"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error: {e}"

    def generate_fix_for_issue(self, issue: CodeIssue) -> Improvement:
        """Generate improvement for a specific issue"""
        prompt = f"""Given this code issue:
File: {issue.file}
Line: {issue.line}
Issue: {issue.issue}
Current code: {issue.code_snippet}

Provide:
1. Detailed explanation
2. Specific code fix
3. Why this improves the code

Be concise and specific."""

        response = self.query(prompt)

        return Improvement(
            id=f"fix_{Path(issue.file).stem}_{issue.line}",
            priority=issue.severity,
            category=issue.category,
            title=issue.issue,
            description=response[:200],
            affected_files=[issue.file],
            impact_score=self._calculate_impact(issue),
            effort_score=self._calculate_effort(issue),
            implementation=response
        )

    def _calculate_impact(self, issue: CodeIssue) -> float:
        """Calculate impact score"""
        severity_map = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.3
        }
        return severity_map.get(issue.severity, 0.5)

    def _calculate_effort(self, issue: CodeIssue) -> float:
        """Calculate effort score (lower is easier)"""
        category_effort = {
            "style": 0.2,
            "quality": 0.4,
            "performance": 0.6,
            "security": 0.8
        }
        return category_effort.get(issue.category, 0.5)


class ContinuousImprover:
    """Main improvement system"""

    def __init__(self, repo_path: Path, ollama_url: str = "http://localhost:11434"):
        self.repo_path = Path(repo_path)
        self.analyzer = StaticAnalyzer()
        self.generator = ImprovementGenerator(ollama_url)

    def analyze_codebase(self) -> List[CodeIssue]:
        """Analyze entire codebase"""
        print("\n🔍 Analyzing codebase...")

        issues = []
        py_files = list(self.repo_path.rglob("*.py"))

        for py_file in py_files:
            # Skip test files and venv
            if 'test' in str(py_file) or 'venv' in str(py_file) or '.venv' in str(py_file):
                continue

            print(f"  Analyzing {py_file.name}...", end=" ")
            file_issues = self.analyzer.analyze_python_file(py_file)
            issues.extend(file_issues)
            print(f"({len(file_issues)} issues)")

        return issues

    def generate_improvements(self, issues: List[CodeIssue], max_improvements: int = 10) -> List[Improvement]:
        """Generate improvement suggestions"""
        print(f"\n💡 Generating improvements for top {max_improvements} issues...")

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 99))

        improvements = []
        for issue in sorted_issues[:max_improvements]:
            print(f"  {issue.severity.upper()}: {issue.issue[:50]}...")
            improvement = self.generator.generate_fix_for_issue(issue)
            improvements.append(improvement)

        return improvements

    def prioritize_improvements(self, improvements: List[Improvement]) -> List[Improvement]:
        """Prioritize improvements by impact/effort ratio"""
        def priority_score(imp: Improvement) -> float:
            # Higher impact, lower effort = higher score
            return imp.impact_score / max(imp.effort_score, 0.1)

        return sorted(improvements, key=priority_score, reverse=True)

    def generate_report(self, issues: List[CodeIssue], improvements: List[Improvement]) -> str:
        """Generate improvement report"""
        report = f"""# Code Improvement Report
Generated: {datetime.utcnow().isoformat()}

## Summary
- **Total Issues Found:** {len(issues)}
- **Improvements Suggested:** {len(improvements)}

### Issues by Severity
"""

        # Count by severity
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            report += f"- **{severity.upper()}:** {count}\n"

        report += "\n### Issues by Category\n"

        # Count by category
        category_counts = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{category}:** {count}\n"

        report += "\n## Top Priority Improvements\n\n"

        prioritized = self.prioritize_improvements(improvements)

        for i, imp in enumerate(prioritized[:5], 1):
            report += f"### {i}. {imp.title}\n\n"
            report += f"- **Priority:** {imp.priority}\n"
            report += f"- **Category:** {imp.category}\n"
            report += f"- **Impact:** {imp.impact_score:.2f}/1.00\n"
            report += f"- **Effort:** {imp.effort_score:.2f}/1.00\n"
            report += f"- **Files:** {', '.join(imp.affected_files)}\n\n"
            report += f"**Description:**\n{imp.description}\n\n"
            report += "---\n\n"

        return report

    def run_improvement_cycle(self) -> Dict:
        """Run complete improvement cycle"""
        print("\n" + "="*70)
        print("CONTINUOUS IMPROVEMENT CYCLE")
        print("="*70)

        # Analyze
        issues = self.analyze_codebase()

        print(f"\n📊 Found {len(issues)} total issues")

        if not issues:
            print("✅ No issues found!")
            return {"issues": [], "improvements": []}

        # Generate improvements
        improvements = self.generate_improvements(issues, max_improvements=min(10, len(issues)))

        # Generate report
        report = self.generate_report(issues, improvements)

        return {
            "issues": issues,
            "improvements": improvements,
            "report": report
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Real Continuous Improvement System")
    parser.add_argument("--repo-path", default=".", help="Repository path")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--model", default="codellama", help="Ollama model")
    parser.add_argument("--report", default="improvement_report.md", help="Output report")
    parser.add_argument("--json", help="Save JSON output")

    args = parser.parse_args()

    # Check Ollama
    try:
        requests.get(f"{args.ollama_url}/api/tags", timeout=5).raise_for_status()
    except:
        print(f"❌ Cannot connect to Ollama at {args.ollama_url}")
        return 1

    # Run improvement cycle
    improver = ContinuousImprover(Path(args.repo_path), args.ollama_url)
    results = improver.run_improvement_cycle()

    # Save report
    with open(args.report, 'w') as f:
        f.write(results["report"])

    print(f"\n💾 Report saved to {args.report}")

    # Save JSON if requested
    if args.json:
        json_data = {
            "issues": [
                {
                    "file": i.file,
                    "line": i.line,
                    "severity": i.severity,
                    "category": i.category,
                    "issue": i.issue,
                    "suggestion": i.suggestion
                }
                for i in results["issues"]
            ],
            "improvements": [
                {
                    "id": imp.id,
                    "priority": imp.priority,
                    "category": imp.category,
                    "title": imp.title,
                    "impact_score": imp.impact_score,
                    "effort_score": imp.effort_score
                }
                for imp in results["improvements"]
            ]
        }

        with open(args.json, 'w') as f:
            json.dump(json_data, f, indent=2)

        print(f"💾 JSON saved to {args.json}")

    print("\n✅ Improvement cycle complete!")
    return 0


if __name__ == "__main__":
    exit(main())
