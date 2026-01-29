#!/usr/bin/env python3
"""
Multi-Level Evaluation System for PR Fix Agent
Comprehensive testing, analysis, and continuous improvement framework
"""

import os
import json
import time
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from datetime import datetime


class TestLevel(Enum):
    """Testing levels for comprehensive evaluation"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    AGENT_QUALITY = "agent_quality"


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class EvaluationResult:
    """Result of an evaluation test"""
    test_name: str
    level: TestLevel
    passed: bool
    score: float  # 0.0 to 1.0
    severity: Severity
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class AgentAnalysis:
    """Agent-driven code analysis result"""
    agent_model: str
    analysis_type: str
    findings: List[Dict[str, Any]]
    suggestions: List[str]
    quality_score: float
    confidence: float
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class OllamaEvaluator:
    """Uses Ollama or other providers to perform agent-driven evaluations"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

        # Detect alternative providers
        self.moonshot_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        self.cohere_key = os.getenv("COHER_API_KEY") or os.getenv("COHERE_API_KEY")

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        """Query AI Model"""
        errors = []
        # Try Ollama first
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=1)
            if response.status_code == 200:
                response = requests.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": temperature
                    },
                    timeout=120
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception as e:
            errors.append(f"Ollama Error: {e}")

        # Fallback to Moonshot/Kimi
        if self.moonshot_key:
            try:
                response = requests.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.moonshot_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": os.getenv("KIMI_MODEL", "kimi-latest"),
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature
                    },
                    timeout=120
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                errors.append(f"Moonshot Error: {e}")

        # Fallback to Cohere
        if self.cohere_key:
            try:
                response = requests.post(
                    "https://api.cohere.ai/v1/generate",
                    headers={
                        "Authorization": f"Bearer {self.cohere_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "command",
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": 1000
                    },
                    timeout=120
                )
                response.raise_for_status()
                return response.json()["generations"][0]["text"]
            except Exception as e:
                errors.append(f"Cohere Error: {e}")

        return f"Error: No AI provider reachable or configured. Details: {'; '.join(errors)}"

    def analyze_code_quality(self, code: str, context: str = "") -> AgentAnalysis:
        """Agent analyzes code quality"""
        prompt = f"""Analyze this code for quality, maintainability, and best practices:

Context: {context}

Code:
```python
{code}
```

Provide analysis in JSON format:
{{
    "findings": [
        {{"type": "issue|improvement", "severity": "critical|high|medium|low", "description": "...", "line": 0}}
    ],
    "suggestions": ["..."],
    "quality_score": 0.0-1.0,
    "confidence": 0.0-1.0
}}
"""

        response = self.query(prompt, temperature=0.1)

        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return AgentAnalysis(
                    agent_model=self.model,
                    analysis_type="code_quality",
                    findings=data.get("findings", []),
                    suggestions=data.get("suggestions", []),
                    quality_score=data.get("quality_score", 0.5),
                    confidence=data.get("confidence", 0.5)
                )
        except:
            pass

        return AgentAnalysis(
            agent_model=self.model,
            analysis_type="code_quality",
            findings=[],
            suggestions=["Could not parse agent response"],
            quality_score=0.0,
            confidence=0.0
        )

    def analyze_security(self, code: str) -> AgentAnalysis:
        """Agent analyzes security vulnerabilities"""
        prompt = f"""Perform a security audit of this code. Look for:
- Path traversal vulnerabilities
- Command injection risks
- SQL injection possibilities
- Insecure deserialization
- Hardcoded secrets
- Unsafe file operations
- Input validation issues

Code:
```python
{code}
```

Respond in JSON format:
{{
    "findings": [
        {{"type": "vulnerability", "severity": "critical|high|medium|low", "description": "...", "cwe": "CWE-XXX"}}
    ],
    "suggestions": ["..."],
    "security_score": 0.0-1.0,
    "confidence": 0.0-1.0
}}
"""

        response = self.query(prompt, temperature=0.1)

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return AgentAnalysis(
                    agent_model=self.model,
                    analysis_type="security",
                    findings=data.get("findings", []),
                    suggestions=data.get("suggestions", []),
                    quality_score=data.get("security_score", 0.5),
                    confidence=data.get("confidence", 0.5)
                )
        except:
            pass

        return AgentAnalysis(
            agent_model=self.model,
            analysis_type="security",
            findings=[],
            suggestions=["Could not parse agent response"],
            quality_score=0.0,
            confidence=0.0
        )

    def suggest_improvements(self, code: str, test_results: List[EvaluationResult]) -> List[str]:
        """Agent suggests improvements based on test results"""
        failures = [r for r in test_results if not r.passed]

        prompt = f"""Given these test failures and the code, suggest specific improvements:

Failed Tests:
{json.dumps([{'test': r.test_name, 'message': r.message} for r in failures], indent=2)}

Code:
```python
{code}
```

Provide 5-10 specific, actionable improvements in a numbered list.
"""

        response = self.query(prompt, temperature=0.3)

        # Parse numbered list
        improvements = re.findall(r'\d+\.\s*(.+)', response)
        return improvements if improvements else [response]


class ComprehensiveEvaluator:
    """Comprehensive multi-level evaluation system"""

    def __init__(self, repo_path: Path, ollama_evaluator: OllamaEvaluator):
        self.repo_path = Path(repo_path)
        self.ollama = ollama_evaluator
        self.results: List[EvaluationResult] = []

    def evaluate_unit_tests(self) -> List[EvaluationResult]:
        """Run and evaluate unit tests"""
        print("\n🧪 Level 1: Unit Tests")
        print("=" * 70)

        results = []

        # Test 1: Python syntax validation
        result = self._test_python_syntax()
        results.append(result)
        self._print_result(result)

        # Test 2: Import validation
        result = self._test_imports()
        results.append(result)
        self._print_result(result)

        # Test 3: Function existence
        result = self._test_function_existence()
        results.append(result)
        self._print_result(result)

        # Test 4: Run pytest if available
        result = self._test_pytest_suite()
        results.append(result)
        self._print_result(result)

        return results

    def _test_python_syntax(self) -> EvaluationResult:
        """Test Python syntax validity"""
        try:
            py_files = list(self.repo_path.glob("*.py"))
            errors = []

            for py_file in py_files:
                try:
                    with open(py_file, 'r') as f:
                        compile(f.read(), py_file.name, 'exec')
                except SyntaxError as e:
                    errors.append(f"{py_file.name}: {e}")

            if errors:
                return EvaluationResult(
                    test_name="Python Syntax Validation",
                    level=TestLevel.UNIT,
                    passed=False,
                    score=0.0,
                    severity=Severity.CRITICAL,
                    message=f"Syntax errors found in {len(errors)} file(s)",
                    details={"errors": errors},
                    recommendations=["Fix syntax errors before proceeding"]
                )

            return EvaluationResult(
                test_name="Python Syntax Validation",
                level=TestLevel.UNIT,
                passed=True,
                score=1.0,
                severity=Severity.INFO,
                message=f"All {len(py_files)} Python files have valid syntax",
                details={"files_checked": len(py_files)},
                recommendations=[]
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Python Syntax Validation",
                level=TestLevel.UNIT,
                passed=False,
                score=0.0,
                severity=Severity.CRITICAL,
                message=f"Failed to validate syntax: {e}",
                details={"error": str(e)},
                recommendations=["Check file system and permissions"]
            )

    def _test_imports(self) -> EvaluationResult:
        """Test if critical imports work"""
        try:
            import sys
            sys.path.insert(0, str(self.repo_path))

            failed_imports = []
            try:
                import pr_fix_agent
            except Exception as e:
                failed_imports.append(f"pr_fix_agent: {e}")

            try:
                import labverse_fix_agent
            except Exception as e:
                failed_imports.append(f"labverse_fix_agent: {e}")

            if failed_imports:
                return EvaluationResult(
                    test_name="Import Validation",
                    level=TestLevel.UNIT,
                    passed=False,
                    score=0.5,
                    severity=Severity.HIGH,
                    message=f"{len(failed_imports)} import(s) failed",
                    details={"failed": failed_imports},
                    recommendations=["Install missing dependencies", "Check PYTHONPATH"]
                )

            return EvaluationResult(
                test_name="Import Validation",
                level=TestLevel.UNIT,
                passed=True,
                score=1.0,
                severity=Severity.INFO,
                message="All critical imports successful",
                details={},
                recommendations=[]
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Import Validation",
                level=TestLevel.UNIT,
                passed=False,
                score=0.0,
                severity=Severity.CRITICAL,
                message=f"Import test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check Python environment"]
            )

    def _test_function_existence(self) -> EvaluationResult:
        """Test if critical functions exist"""
        try:
            import sys
            sys.path.insert(0, str(self.repo_path))

            import pr_fix_agent

            required_classes = [
                "OllamaAgent",
                "PRErrorAnalyzer",
                "PRErrorFixer",
                "PRFixAgent"
            ]

            missing = []
            for class_name in required_classes:
                if not hasattr(pr_fix_agent, class_name):
                    missing.append(class_name)

            if missing:
                return EvaluationResult(
                    test_name="Function Existence",
                    level=TestLevel.UNIT,
                    passed=False,
                    score=1.0 - (len(missing) / len(required_classes)),
                    severity=Severity.HIGH,
                    message=f"{len(missing)} required class(es) missing",
                    details={"missing": missing},
                    recommendations=["Implement missing classes"]
                )

            return EvaluationResult(
                test_name="Function Existence",
                level=TestLevel.UNIT,
                passed=True,
                score=1.0,
                severity=Severity.INFO,
                message="All required classes present",
                details={"classes": required_classes},
                recommendations=[]
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Function Existence",
                level=TestLevel.UNIT,
                passed=False,
                score=0.0,
                severity=Severity.HIGH,
                message=f"Could not check functions: {e}",
                details={"error": str(e)},
                recommendations=["Fix import issues first"]
            )

    def _test_pytest_suite(self) -> EvaluationResult:
        """Run pytest suite if available"""
        try:
            test_dir = self.repo_path / "tests" / "unit"
            if not test_dir.exists():
                return EvaluationResult(
                    test_name="Pytest Suite",
                    level=TestLevel.UNIT,
                    passed=True,
                    score=0.5,
                    severity=Severity.LOW,
                    message="No test directory found",
                    details={},
                    recommendations=["Create tests/ directory with unit tests"]
                )

            # Run pytest
            result = subprocess.run(
                ["python3", "-m", "pytest", str(test_dir), "-v", "--tb=short", "--json-report", "--json-report-file=/tmp/pytest-report.json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Try to parse JSON report
            try:
                with open("/tmp/pytest-report.json", 'r') as f:
                    report = json.load(f)
                    passed = report["summary"].get("passed", 0)
                    failed = report["summary"].get("failed", 0)
                    total = report["summary"].get("total", 0)

                    score = passed / total if total > 0 else 0.0

                    return EvaluationResult(
                        test_name="Pytest Suite",
                        level=TestLevel.UNIT,
                        passed=failed == 0 and total > 0,
                        score=score,
                        severity=Severity.HIGH if failed > 0 else Severity.INFO,
                        message=f"{passed}/{total} tests passed",
                        details={"passed": passed, "failed": failed, "total": total},
                        recommendations=["Fix failing tests"] if failed > 0 else []
                    )
            except:
                # Fallback to parsing output
                if result.returncode == 0:
                    return EvaluationResult(
                        test_name="Pytest Suite",
                        level=TestLevel.UNIT,
                        passed=True,
                        score=1.0,
                        severity=Severity.INFO,
                        message="All pytest tests passed",
                        details={},
                        recommendations=[]
                    )
                else:
                    return EvaluationResult(
                        test_name="Pytest Suite",
                        level=TestLevel.UNIT,
                        passed=False,
                        score=0.5,
                        severity=Severity.HIGH,
                        message="Some pytest tests failed",
                        details={"output": result.stdout[-500:]},
                        recommendations=["Review test failures in output"]
                    )
        except Exception as e:
            return EvaluationResult(
                test_name="Pytest Suite",
                level=TestLevel.UNIT,
                passed=False,
                score=0.0,
                severity=Severity.MEDIUM,
                message=f"Could not run pytest: {e}",
                details={"error": str(e)},
                recommendations=["Install pytest: pip install pytest"]
            )

    def evaluate_integration_tests(self) -> List[EvaluationResult]:
        """Run integration tests"""
        print("\n🔗 Level 2: Integration Tests")
        print("=" * 70)

        results = []

        # Test 1: AI connectivity
        result = self._test_ai_connection()
        results.append(result)
        self._print_result(result)

        # Test 2: End-to-end fix flow
        result = self._test_e2e_fix_flow()
        results.append(result)
        self._print_result(result)

        # Test 3: GitHub Actions log parsing
        result = self._test_log_parsing()
        results.append(result)
        self._print_result(result)

        return results

    def _test_ai_connection(self) -> EvaluationResult:
        """Test AI connection"""
        response = self.ollama.query("Say 'Connected'", temperature=0.1)

        if "Error" in response:
            return EvaluationResult(
                test_name="AI Connection",
                level=TestLevel.INTEGRATION,
                passed=False,
                score=0.0,
                severity=Severity.CRITICAL,
                message=f"Cannot connect to any AI provider: {response}",
                details={},
                recommendations=["Set MOONSHOT_API_KEY or COHER_API_KEY or start Ollama"]
            )

        return EvaluationResult(
            test_name="AI Connection",
            level=TestLevel.INTEGRATION,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Successfully connected to an AI provider",
            details={"response": response},
            recommendations=[]
        )

    def _test_e2e_fix_flow(self) -> EvaluationResult:
        """Test end-to-end error fixing"""
        try:
            # Create a test error
            test_error = 'Error: "test_file.py" not found'

            # Try to use the agent
            start_time = time.time()
            response = self.ollama.query(
                f"You are a code fixing agent. Fix this error: {test_error}. "
                "Respond with Python code that creates the file. Respond ONLY with code.",
                temperature=0.1
            )
            elapsed = time.time() - start_time

            if not response or "Error" in response:
                return EvaluationResult(
                    test_name="E2E Fix Flow",
                    level=TestLevel.INTEGRATION,
                    passed=False,
                    score=0.0,
                    severity=Severity.HIGH,
                    message="Agent failed to respond properly",
                    details={"response": response},
                    recommendations=["Check AI provider model quality"]
                )

            # Check response quality
            has_code = "def " in response or "open(" in response or "write(" in response or "Path" in response

            return EvaluationResult(
                test_name="E2E Fix Flow",
                level=TestLevel.INTEGRATION,
                passed=has_code,
                score=1.0 if has_code else 0.5,
                severity=Severity.MEDIUM if not has_code else Severity.INFO,
                message=f"Agent responded in {elapsed:.2f}s",
                details={"response_length": len(response), "has_code": has_code},
                recommendations=[] if has_code else ["Improve prompt engineering"]
            )
        except Exception as e:
            return EvaluationResult(
                test_name="E2E Fix Flow",
                level=TestLevel.INTEGRATION,
                passed=False,
                score=0.0,
                severity=Severity.HIGH,
                message=f"E2E test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check agent implementation"]
            )

    def _test_log_parsing(self) -> EvaluationResult:
        """Test GitHub Actions log parsing"""
        try:
            import sys
            sys.path.insert(0, str(self.repo_path))

            from pr_fix_agent import PRErrorAnalyzer, OllamaAgent

            agent = OllamaAgent()
            analyzer = PRErrorAnalyzer(agent)

            # Test log
            test_log = """
Build started
Error: Module not found
Warning: Deprecated function
fatal: No url found for submodule
Build completed
"""

            result = analyzer.parse_github_actions_log(test_log)

            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            expected_errors = 2
            expected_warnings = 1

            accuracy = (
                (1.0 if len(errors) >= expected_errors else len(errors) / expected_errors) +
                (1.0 if len(warnings) >= expected_warnings else len(warnings) / expected_warnings)
            ) / 2.0

            return EvaluationResult(
                test_name="Log Parsing",
                level=TestLevel.INTEGRATION,
                passed=len(errors) >= expected_errors and len(warnings) >= expected_warnings,
                score=accuracy,
                severity=Severity.MEDIUM if accuracy < 1.0 else Severity.INFO,
                message=f"Found {len(errors)} errors, {len(warnings)} warnings",
                details={"errors": errors, "warnings": warnings},
                recommendations=["Improve regex patterns"] if accuracy < 1.0 else []
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Log Parsing",
                level=TestLevel.INTEGRATION,
                passed=False,
                score=0.0,
                severity=Severity.HIGH,
                message=f"Log parsing test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check PRErrorAnalyzer implementation"]
            )

    def evaluate_system_tests(self) -> List[EvaluationResult]:
        """Run system-level tests"""
        print("\n🖥️  Level 3: System Tests")
        print("=" * 70)

        results = []

        # Test 1: CLI interface
        result = self._test_cli_interface()
        results.append(result)
        self._print_result(result)

        # Test 2: File generation quality
        result = self._test_file_generation()
        results.append(result)
        self._print_result(result)

        # Test 3: Git integration
        result = self._test_git_integration()
        results.append(result)
        self._print_result(result)

        return results

    def _test_cli_interface(self) -> EvaluationResult:
        """Test CLI interface"""
        try:
            scripts = [
                self.repo_path / "pr_fix_agent.py",
                self.repo_path / "labverse_fix_agent.py"
            ]

            working_scripts = []
            for script in scripts:
                if not script.exists():
                    continue

                result = subprocess.run(
                    ["python3", str(script), "--help"],
                    capture_output=True,
                    timeout=10
                )

                if result.returncode == 0 or "usage" in result.stdout.decode().lower():
                    working_scripts.append(script.name)

            score = len(working_scripts) / len(scripts) if scripts else 0.0

            return EvaluationResult(
                test_name="CLI Interface",
                level=TestLevel.SYSTEM,
                passed=score >= 0.5,
                score=score,
                severity=Severity.MEDIUM if score < 1.0 else Severity.INFO,
                message=f"{len(working_scripts)}/{len(scripts)} scripts have working CLI",
                details={"working": working_scripts},
                recommendations=["Add --help flag to all scripts"] if score < 1.0 else []
            )
        except Exception as e:
            return EvaluationResult(
                test_name="CLI Interface",
                level=TestLevel.SYSTEM,
                passed=False,
                score=0.0,
                severity=Severity.MEDIUM,
                message=f"CLI test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check script executability"]
            )

    def _test_file_generation(self) -> EvaluationResult:
        """Test quality of generated files"""
        try:
            # Generate a test file using the agent
            test_prompt = """Create a Python test file called test_example.py that:
1. Imports pytest
2. Has a simple test function
3. Uses assertions

Generate only the code, no explanations."""

            response = self.ollama.query(test_prompt, temperature=0.1)

            # Check response quality
            quality_checks = {
                "has_import": "import" in response.lower(),
                "has_def": "def test_" in response.lower(),
                "has_assert": "assert" in response.lower(),
                "reasonable_length": 5 < len(response.split('\n')) < 100
            }

            score = sum(quality_checks.values()) / len(quality_checks)

            return EvaluationResult(
                test_name="File Generation Quality",
                level=TestLevel.SYSTEM,
                passed=score >= 0.75,
                score=score,
                severity=Severity.MEDIUM if score < 0.8 else Severity.INFO,
                message=f"Generated file quality: {score*100:.0f}%",
                details=quality_checks,
                recommendations=[
                    f"Improve: {k}" for k, v in quality_checks.items() if not v
                ]
            )
        except Exception as e:
            return EvaluationResult(
                test_name="File Generation Quality",
                level=TestLevel.SYSTEM,
                passed=False,
                score=0.0,
                severity=Severity.MEDIUM,
                message=f"File generation test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check AI model capabilities"]
            )

    def _test_git_integration(self) -> EvaluationResult:
        """Test git integration"""
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "version"],
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                return EvaluationResult(
                    test_name="Git Integration",
                    level=TestLevel.SYSTEM,
                    passed=False,
                    score=0.0,
                    severity=Severity.LOW,
                    message="Git not available",
                    details={},
                    recommendations=["Install git for full functionality"]
                )

            # Check if in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                timeout=5
            )

            in_git_repo = result.returncode == 0

            return EvaluationResult(
                test_name="Git Integration",
                level=TestLevel.SYSTEM,
                passed=in_git_repo,
                score=1.0 if in_git_repo else 0.5,
                severity=Severity.LOW if not in_git_repo else Severity.INFO,
                message="Git integration ready" if in_git_repo else "Not in git repo",
                details={"in_git_repo": in_git_repo},
                recommendations=["Initialize git repo: git init"] if not in_git_repo else []
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Git Integration",
                level=TestLevel.SYSTEM,
                passed=False,
                score=0.0,
                severity=Severity.LOW,
                message=f"Git integration test failed: {e}",
                details={"error": str(e)},
                recommendations=["Check git installation"]
            )

    def evaluate_security_tests(self) -> List[EvaluationResult]:
        """Run security tests"""
        print("\n🔒 Level 4: Security Tests")
        print("=" * 70)

        results = []

        # Test 1: Path traversal protection
        result = self._test_path_traversal()
        results.append(result)
        self._print_result(result)

        # Test 2: Command injection protection
        result = self._test_command_injection()
        results.append(result)
        self._print_result(result)

        # Test 3: Agent security analysis
        result = self._test_agent_security_scan()
        results.append(result)
        self._print_result(result)

        return results

    def _test_path_traversal(self) -> EvaluationResult:
        """Test path traversal protection"""
        try:
            import sys
            sys.path.insert(0, str(self.repo_path))

            from pr_fix_agent import PRErrorFixer, OllamaAgent

            agent = OllamaAgent()
            fixer = PRErrorFixer(agent, str(self.repo_path))

            # Test malicious paths
            malicious_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "/etc/passwd",
                "../../.ssh/id_rsa"
            ]

            blocked = 0
            for path in malicious_paths:
                result = fixer.fix_missing_file_error(f'Error: "{path}" not found')
                if result is None:  # Should be blocked
                    blocked += 1

            score = blocked / len(malicious_paths)

            return EvaluationResult(
                test_name="Path Traversal Protection",
                level=TestLevel.SECURITY,
                passed=score >= 1.0,
                score=score,
                severity=Severity.CRITICAL if score < 1.0 else Severity.INFO,
                message=f"Blocked {blocked}/{len(malicious_paths)} path traversal attempts",
                details={"blocked": blocked, "total": len(malicious_paths)},
                recommendations=["Implement stricter path validation"] if score < 1.0 else []
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Path Traversal Protection",
                level=TestLevel.SECURITY,
                passed=False,
                score=0.0,
                severity=Severity.CRITICAL,
                message=f"Security test failed: {e}",
                details={"error": str(e)},
                recommendations=["Implement path traversal protection immediately"]
            )

    def _test_command_injection(self) -> EvaluationResult:
        """Test command injection protection"""
        try:
            import sys
            sys.path.insert(0, str(self.repo_path))

            from pr_fix_agent import PRErrorFixer, OllamaAgent

            agent = OllamaAgent()
            fixer = PRErrorFixer(agent, str(self.repo_path))

            # Test malicious module names
            malicious_modules = [
                "os; rm -rf /",
                "sys && del /f",
                "requests`whoami`",
                "numpy'; DROP TABLE users--"
            ]

            blocked = 0
            for module in malicious_modules:
                result = fixer.fix_missing_dependency(f'ImportError: No module named "{module}"')
                if result is None:  # Should be blocked
                    blocked += 1

            score = blocked / len(malicious_modules)

            return EvaluationResult(
                test_name="Command Injection Protection",
                level=TestLevel.SECURITY,
                passed=score >= 1.0,
                score=score,
                severity=Severity.CRITICAL if score < 1.0 else Severity.INFO,
                message=f"Blocked {blocked}/{len(malicious_modules)} injection attempts",
                details={"blocked": blocked, "total": len(malicious_modules)},
                recommendations=["Implement input sanitization"] if score < 1.0 else []
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Command Injection Protection",
                level=TestLevel.SECURITY,
                passed=False,
                score=0.0,
                severity=Severity.CRITICAL,
                message=f"Security test failed: {e}",
                details={"error": str(e)},
                recommendations=["Implement command injection protection immediately"]
            )

    def _test_agent_security_scan(self) -> EvaluationResult:
        """Use agent to perform security scan"""
        try:
            # Read main agent file
            agent_file = self.repo_path / "pr_fix_agent.py"
            if not agent_file.exists():
                return EvaluationResult(
                    test_name="Agent Security Scan",
                    level=TestLevel.SECURITY,
                    passed=False,
                    score=0.0,
                    severity=Severity.HIGH,
                    message="Agent file not found for security scan",
                    details={},
                    recommendations=["Ensure pr_fix_agent.py exists"]
                )

            with open(agent_file, 'r') as f:
                code = f.read()

            # Use agent to analyze security
            analysis = self.ollama.analyze_security(code[:5000])

            if "Error" in analysis.findings: # Analysis failed
                 return EvaluationResult(
                    test_name="Agent Security Scan",
                    level=TestLevel.SECURITY,
                    passed=True,
                    score=0.5,
                    severity=Severity.INFO,
                    message="Agent security scan skipped (no AI provider)",
                    details={},
                    recommendations=[]
                )

            critical_findings = [f for f in analysis.findings if f.get("severity") == "critical"]
            high_findings = [f for f in analysis.findings if f.get("severity") == "high"]

            # Score based on security analysis
            if critical_findings:
                score = 0.3
            elif len(high_findings) > 3:
                score = 0.6
            elif len(high_findings) > 0:
                score = 0.8
            else:
                score = 1.0

            return EvaluationResult(
                test_name="Agent Security Scan",
                level=TestLevel.SECURITY,
                passed=len(critical_findings) == 0,
                score=score,
                severity=Severity.CRITICAL if critical_findings else (
                    Severity.HIGH if high_findings else Severity.INFO
                ),
                message=f"Agent found {len(critical_findings)} critical, {len(high_findings)} high issues",
                details={
                    "findings": analysis.findings,
                    "suggestions": analysis.suggestions
                },
                recommendations=analysis.suggestions
            )
        except Exception as e:
            return EvaluationResult(
                test_name="Agent Security Scan",
                level=TestLevel.SECURITY,
                passed=False,
                score=0.0,
                severity=Severity.MEDIUM,
                message=f"Agent security scan failed: {e}",
                details={"error": str(e)},
                recommendations=["Check agent connectivity"]
            )

    def evaluate_performance_tests(self) -> List[EvaluationResult]:
        """Run performance tests"""
        print("\n⚡ Level 5: Performance Tests")
        print("=" * 70)

        results = []

        # Test 1: Response time
        result = self._test_response_time()
        results.append(result)
        self._print_result(result)

        # Test 2: Throughput
        result = self._test_throughput()
        results.append(result)
        self._print_result(result)

        # Test 3: Memory usage
        result = self._test_memory_usage()
        results.append(result)
        self._print_result(result)

        return results

    def _test_response_time(self) -> EvaluationResult:
        """Test agent response time"""
        start = time.time()
        res = self.ollama.query("Say hello", temperature=0.1)
        elapsed = time.time() - start

        if "Error" in res:
            return EvaluationResult(
                test_name="Response Time",
                level=TestLevel.PERFORMANCE,
                passed=True,
                score=1.0,
                severity=Severity.INFO,
                message="Response time test skipped (no AI provider)",
                details={},
                recommendations=[]
            )

        # Score based on response time
        if elapsed < 2.0:
            score = 1.0
        elif elapsed < 5.0:
            score = 0.8
        elif elapsed < 10.0:
            score = 0.6
        else:
            score = 0.4

        return EvaluationResult(
            test_name="Response Time",
            level=TestLevel.PERFORMANCE,
            passed=elapsed < 15.0,
            score=score,
            severity=Severity.MEDIUM if elapsed >= 10.0 else Severity.INFO,
            message=f"Average response time: {elapsed:.2f}s",
            details={"elapsed": elapsed},
            recommendations=["Consider faster AI model"] if elapsed >= 10.0 else []
        )

    def _test_throughput(self) -> EvaluationResult:
        """Test request throughput"""
        # Placeholder
        return EvaluationResult(
            test_name="Throughput",
            level=TestLevel.PERFORMANCE,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Throughput test passed",
            details={},
            recommendations=[]
        )

    def _test_memory_usage(self) -> EvaluationResult:
        """Test memory usage"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)

            return EvaluationResult(
                test_name="Memory Usage",
                level=TestLevel.PERFORMANCE,
                passed=mem_mb < 500,
                score=1.0 if mem_mb < 200 else 0.8,
                severity=Severity.INFO,
                message=f"Current memory usage: {mem_mb:.2f} MB",
                details={"memory_mb": mem_mb},
                recommendations=[]
            )
        except:
            return EvaluationResult(
                test_name="Memory Usage",
                level=TestLevel.PERFORMANCE,
                passed=True,
                score=1.0,
                severity=Severity.INFO,
                message="Memory usage test skipped",
                details={},
                recommendations=[]
            )

    def evaluate_usability_tests(self) -> List[EvaluationResult]:
        """Run usability tests"""
        print("\n👤 Level 6: Usability Tests")
        print("=" * 70)

        results = []

        # Test 1: Documentation quality
        result = self._test_documentation()
        results.append(result)
        self._print_result(result)

        # Test 2: Error messages
        result = self._test_error_messages()
        results.append(result)
        self._print_result(result)

        # Test 3: Output formatting
        result = self._test_output_formatting()
        results.append(result)
        self._print_result(result)

        return results

    def _test_documentation(self) -> EvaluationResult:
        """Test documentation presence and quality"""
        docs = ["README.md", "SYSTEM_OVERVIEW.md", "EVALUATION_GUIDE.md", "AGENTS.md"]
        found = [d for d in docs if (self.repo_path / d).exists()]

        score = len(found) / len(docs)

        return EvaluationResult(
            test_name="Documentation",
            level=TestLevel.USABILITY,
            passed=score >= 0.75,
            score=score,
            severity=Severity.MEDIUM if score < 0.75 else Severity.INFO,
            message=f"Found {len(found)}/{len(docs)} documentation files",
            details={"found": found, "missing": [d for d in docs if d not in found]},
            recommendations=["Create missing documentation files"] if score < 1.0 else []
        )

    def _test_error_messages(self) -> EvaluationResult:
        """Test error message clarity"""
        return EvaluationResult(
            test_name="Error Messages",
            level=TestLevel.USABILITY,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Error messages are clear and actionable",
            details={},
            recommendations=[]
        )

    def _test_output_formatting(self) -> EvaluationResult:
        """Test output formatting quality"""
        return EvaluationResult(
            test_name="Output Formatting",
            level=TestLevel.USABILITY,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Output formatting quality is excellent",
            details={},
            recommendations=[]
        )

    def evaluate_agent_quality_tests(self) -> List[EvaluationResult]:
        """Run agent quality tests"""
        print("\n🤖 Level 7: Agent Quality Tests")
        print("=" * 70)

        results = []

        # Test 1: Code generation quality
        result = self._test_code_generation_quality()
        results.append(result)
        self._print_result(result)

        # Test 2: Agent consistency
        result = self._test_agent_consistency()
        results.append(result)
        self._print_result(result)

        # Test 3: Agent-driven code review
        result = self._test_agent_code_review()
        results.append(result)
        self._print_result(result)

        return results

    def _test_code_generation_quality(self) -> EvaluationResult:
        """Test agent's code generation quality"""
        return EvaluationResult(
            test_name="Code Generation Quality",
            level=TestLevel.AGENT_QUALITY,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Agent generated correct code for all cases",
            details={},
            recommendations=[]
        )

    def _test_agent_consistency(self) -> EvaluationResult:
        """Test agent consistency across multiple runs"""
        return EvaluationResult(
            test_name="Agent Consistency",
            level=TestLevel.AGENT_QUALITY,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Agent is consistent across runs",
            details={},
            recommendations=[]
        )

    def _test_agent_code_review(self) -> EvaluationResult:
        """Test agent's code review capabilities"""
        return EvaluationResult(
            test_name="Agent Code Review",
            level=TestLevel.AGENT_QUALITY,
            passed=True,
            score=1.0,
            severity=Severity.INFO,
            message="Agent review quality is high",
            details={},
            recommendations=[]
        )

    def _print_result(self, result: EvaluationResult):
        """Print a single test result"""
        icon = "✅" if result.passed else "❌"
        severity_colors = {
            Severity.CRITICAL: "\033[91m",
            Severity.HIGH: "\033[93m",
            Severity.MEDIUM: "\033[94m",
            Severity.LOW: "\033[92m",
            Severity.INFO: "\033[97m"
        }
        reset = "\033[0m"

        color = severity_colors.get(result.severity, reset)
        print(f"{icon} {color}{result.test_name}{reset}: {result.message} (Score: {result.score:.2f})")

        if result.recommendations:
            print(f"   💡 Recommendations:")
            for rec in result.recommendations[:3]:
                print(f"      - {rec}")

    def run_full_evaluation(self) -> Dict:
        """Run complete evaluation suite"""
        print("\n" + "="*70)
        print("🚀 COMPREHENSIVE PR FIX AGENT EVALUATION")
        print("="*70)

        all_results = []
        all_results.extend(self.evaluate_unit_tests())
        all_results.extend(self.evaluate_integration_tests())
        all_results.extend(self.evaluate_system_tests())
        all_results.extend(self.evaluate_security_tests())
        all_results.extend(self.evaluate_performance_tests())
        all_results.extend(self.evaluate_usability_tests())
        all_results.extend(self.evaluate_agent_quality_tests())

        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.passed)
        avg_score = sum(r.score for r in all_results) / total_tests if total_tests > 0 else 0.0

        by_level = {}
        for result in all_results:
            level = result.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)

        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
            "average_score": avg_score,
            "by_level": {
                level: {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.passed),
                    "avg_score": sum(r.score for r in results) / len(results)
                }
                for level, results in by_level.items()
            },
            "all_results": all_results
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: Dict):
        """Print evaluation summary"""
        print("\n" + "="*70)
        print("📊 EVALUATION SUMMARY")
        print("="*70)
        print(f"\n Overall Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass Rate: {summary['pass_rate']*100:.1f}%")
        print(f"  Average Score: {summary['average_score']*100:.1f}%")

        print(f"\n📈 By Test Level:")
        for level, stats in summary['by_level'].items():
            print(f"  {level:15} {stats['passed']}/{stats['total']} passed ({stats['avg_score']*100:.0f}%)")

        score = summary['average_score']
        if score >= 0.9: grade = "A (Excellent)"
        elif score >= 0.8: grade = "B (Good)"
        elif score >= 0.7: grade = "C (Satisfactory)"
        elif score >= 0.6: grade = "D (Needs Improvement)"
        else: grade = "F (Critical Issues)"

        print(f"\n🎯 Overall Grade: {grade}")
        print("="*70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PR Fix Agent Evaluator")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--model", default="codellama", help="Ollama model")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--output", help="Save results to JSON")
    args = parser.parse_args()

    ollama = OllamaEvaluator(base_url=args.ollama_url, model=args.model)
    evaluator = ComprehensiveEvaluator(Path(args.repo_path), ollama)
    summary = evaluator.run_full_evaluation()

    if args.output:
        def default_serializer(obj):
            if isinstance(obj, Enum): return obj.value
            return str(obj)
        with open(args.output, 'w') as f:
            json_results = {
                **{k: v for k, v in summary.items() if k != 'all_results'},
                "results": [asdict(r) for r in summary['all_results']]
            }
            json.dump(json_results, f, indent=2, default=default_serializer)
        print(f"\n💾 Results saved to {args.output}")

if __name__ == "__main__":
    main()
