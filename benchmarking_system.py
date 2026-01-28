#!/usr/bin/env python3
"""
Benchmarking and Model Comparison System
Compare different Ollama models and track performance over time
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
import statistics


@dataclass
class BenchmarkTest:
    """Represents a single benchmark test"""
    name: str
    category: str  # code_gen, analysis, fixing, security
    prompt: str
    expected_elements: List[str]
    max_time: float  # Maximum acceptable time in seconds
    weight: float = 1.0  # Importance weight


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    test_name: str
    model: str
    success: bool
    response_time: float
    response_length: int
    quality_score: float  # 0.0 to 1.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ModelBenchmark:
    """Complete benchmark results for a model"""
    model: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_response_time: float
    avg_quality_score: float
    overall_score: float
    results: List[BenchmarkResult]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class ModelBenchmarker:
    """Benchmark different Ollama models"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"
        self.tests = self._define_benchmark_tests()

    def _define_benchmark_tests(self) -> List[BenchmarkTest]:
        """Define standard benchmark tests"""
        return [
            # Code Generation Tests
            BenchmarkTest(
                name="Simple Function Generation",
                category="code_gen",
                prompt="Create a Python function called add_numbers that takes two parameters and returns their sum. Generate only code, no explanations.",
                expected_elements=["def add_numbers", "return", "+"],
                max_time=10.0,
                weight=1.0
            ),
            BenchmarkTest(
                name="Class Generation",
                category="code_gen",
                prompt="Create a Python class called Person with __init__ method that takes name and age. Generate only code, no explanations.",
                expected_elements=["class Person", "__init__", "self", "name", "age"],
                max_time=15.0,
                weight=1.5
            ),
            BenchmarkTest(
                name="Test Function Generation",
                category="code_gen",
                prompt="Create a pytest test function that tests if a list is empty. Generate only code, no explanations.",
                expected_elements=["def test_", "assert", "=="],
                max_time=10.0,
                weight=1.0
            ),

            # Error Analysis Tests
            BenchmarkTest(
                name="Import Error Analysis",
                category="analysis",
                prompt='Analyze this error and suggest a fix in one sentence: "ImportError: No module named \'requests\'"',
                expected_elements=["install", "pip", "requests"],
                max_time=8.0,
                weight=1.0
            ),
            BenchmarkTest(
                name="Syntax Error Analysis",
                category="analysis",
                prompt='Analyze this error and suggest a fix in one sentence: "SyntaxError: invalid syntax at line 5"',
                expected_elements=["syntax", "line", "check"],
                max_time=8.0,
                weight=1.0
            ),

            # Error Fixing Tests
            BenchmarkTest(
                name="Fix Missing Import",
                category="fixing",
                prompt='Fix this code by adding the missing import: "import sys\\nimport os\\nresult = json.dumps(data)". Generate only the fixed code.',
                expected_elements=["import json", "import sys", "import os"],
                max_time=10.0,
                weight=1.5
            ),
            BenchmarkTest(
                name="Fix Indentation",
                category="fixing",
                prompt='Fix the indentation in this code: "def test():\\nprint(\\"hello\\")\\nreturn True". Generate only the fixed code.',
                expected_elements=["def test():", "    print", "    return"],
                max_time=10.0,
                weight=1.0
            ),

            # Security Tests
            BenchmarkTest(
                name="Identify Path Traversal",
                category="security",
                prompt='Is this code secure? Explain briefly: "file_path = user_input\\nwith open(file_path) as f: data = f.read()"',
                expected_elements=["path traversal", "validate", "danger"],
                max_time=12.0,
                weight=2.0
            ),
            BenchmarkTest(
                name="Identify SQL Injection",
                category="security",
                prompt='Is this code secure? Explain briefly: "query = f\\"SELECT * FROM users WHERE id = {user_id}\\"\\ncursor.execute(query)"',
                expected_elements=["sql injection", "parameter", "vulnerable"],
                max_time=12.0,
                weight=2.0
            ),

            # Complex Tasks
            BenchmarkTest(
                name="Complete Module Creation",
                category="code_gen",
                prompt="Create a complete Python module with a class that reads a file, processes its content, and writes to another file. Include error handling. Generate only code.",
                expected_elements=["class", "def", "try", "except", "open", "with"],
                max_time=30.0,
                weight=2.5
            ),
        ]

    def query_model(self, model: str, prompt: str, temperature: float = 0.1) -> Tuple[str, float]:
        """Query a model and measure response time"""
        start_time = time.time()

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            result = response.json()["response"]

            return result, elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            return f"Error: {e}", elapsed

    def evaluate_response(self, response: str, test: BenchmarkTest) -> float:
        """Evaluate response quality (0.0 to 1.0)"""
        # Check for errors
        if response.startswith("Error:"):
            return 0.0

        # Count how many expected elements are present
        present = sum(1 for elem in test.expected_elements if elem.lower() in response.lower())
        element_score = present / len(test.expected_elements)

        # Check response length (not too short, not too long)
        length_score = 1.0
        if len(response) < 20:
            length_score = 0.3
        elif len(response) > 5000:
            length_score = 0.8

        # Combine scores
        return (element_score * 0.7 + length_score * 0.3)

    def run_test(self, model: str, test: BenchmarkTest) -> BenchmarkResult:
        """Run a single benchmark test"""
        print(f"  Running: {test.name}...", end=" ")

        response, response_time = self.query_model(model, test.prompt)
        quality_score = self.evaluate_response(response, test)
        success = (
            quality_score >= 0.6 and
            response_time <= test.max_time
        )

        result = BenchmarkResult(
            test_name=test.name,
            model=model,
            success=success,
            response_time=response_time,
            response_length=len(response),
            quality_score=quality_score
        )

        status = "✅" if success else "❌"
        print(f"{status} ({response_time:.2f}s, quality: {quality_score:.2f})")

        return result

    def benchmark_model(self, model: str) -> ModelBenchmark:
        """Run complete benchmark suite for a model"""
        print(f"\n{'='*70}")
        print(f"Benchmarking Model: {model}")
        print(f"{'='*70}")

        results = []

        # Group tests by category
        by_category = {}
        for test in self.tests:
            if test.category not in by_category:
                by_category[test.category] = []
            by_category[test.category].append(test)

        # Run tests by category
        for category, tests in by_category.items():
            print(f"\n📁 Category: {category}")
            for test in tests:
                result = self.run_test(model, test)
                results.append(result)

        # Calculate statistics
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        avg_time = statistics.mean(r.response_time for r in results)
        avg_quality = statistics.mean(r.quality_score for r in results)

        # Calculate overall score (weighted by test importance)
        weighted_scores = []
        for result in results:
            test = next(t for t in self.tests if t.name == result.test_name)
            score = result.quality_score if result.success else 0.0
            weighted_scores.append(score * test.weight)

        total_weight = sum(t.weight for t in self.tests)
        overall_score = sum(weighted_scores) / total_weight

        benchmark = ModelBenchmark(
            model=model,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            avg_response_time=avg_time,
            avg_quality_score=avg_quality,
            overall_score=overall_score,
            results=results
        )

        self._print_benchmark_summary(benchmark)

        return benchmark

    def _print_benchmark_summary(self, benchmark: ModelBenchmark):
        """Print benchmark summary"""
        print(f"\n{'='*70}")
        print(f"📊 Benchmark Summary: {benchmark.model}")
        print(f"{'='*70}")
        print(f"Total Tests: {benchmark.total_tests}")
        print(f"Passed: {benchmark.passed_tests}")
        print(f"Failed: {benchmark.failed_tests}")
        print(f"Pass Rate: {benchmark.passed_tests/benchmark.total_tests*100:.1f}%")
        print(f"Avg Response Time: {benchmark.avg_response_time:.2f}s")
        print(f"Avg Quality Score: {benchmark.avg_quality_score:.2f}")
        print(f"Overall Score: {benchmark.overall_score:.2f}")

        # Grade
        if benchmark.overall_score >= 0.9:
            grade = "A+ (Excellent)"
        elif benchmark.overall_score >= 0.8:
            grade = "A (Very Good)"
        elif benchmark.overall_score >= 0.7:
            grade = "B (Good)"
        elif benchmark.overall_score >= 0.6:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"

        print(f"Grade: {grade}")
        print(f"{'='*70}")

    def compare_models(self, models: List[str]) -> Dict:
        """Compare multiple models"""
        print(f"\n🔬 COMPARING {len(models)} MODELS")
        print(f"{'='*70}\n")

        benchmarks = []

        for model in models:
            try:
                benchmark = self.benchmark_model(model)
                benchmarks.append(benchmark)
            except Exception as e:
                print(f"\n❌ Error benchmarking {model}: {e}")

        if not benchmarks:
            return {"error": "No models successfully benchmarked"}

        # Create comparison
        comparison = {
            "models": [b.model for b in benchmarks],
            "benchmarks": benchmarks,
            "winner": max(benchmarks, key=lambda b: b.overall_score).model,
            "comparison_table": self._create_comparison_table(benchmarks)
        }

        self._print_comparison(comparison)

        return comparison

    def _create_comparison_table(self, benchmarks: List[ModelBenchmark]) -> Dict:
        """Create comparison table"""
        return {
            "overall_scores": {b.model: b.overall_score for b in benchmarks},
            "pass_rates": {b.model: b.passed_tests/b.total_tests for b in benchmarks},
            "avg_response_times": {b.model: b.avg_response_time for b in benchmarks},
            "avg_quality_scores": {b.model: b.avg_quality_score for b in benchmarks}
        }

    def _print_comparison(self, comparison: Dict):
        """Print model comparison"""
        print(f"\n{'='*70}")
        print("📊 MODEL COMPARISON")
        print(f"{'='*70}\n")

        table = comparison["comparison_table"]

        print("Overall Scores:")
        for model, score in sorted(table["overall_scores"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {model:20} {score:.3f} {'🏆' if model == comparison['winner'] else ''}")

        print("\nPass Rates:")
        for model, rate in sorted(table["pass_rates"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {model:20} {rate*100:.1f}%")

        print("\nAvg Response Times:")
        for model, time in sorted(table["avg_response_times"].items(), key=lambda x: x[1]):
            print(f"  {model:20} {time:.2f}s")

        print("\nAvg Quality Scores:")
        for model, quality in sorted(table["avg_quality_scores"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {model:20} {quality:.3f}")

        print(f"\n🏆 Winner: {comparison['winner']}")
        print(f"{'='*70}")


class ProgressTracker:
    """Track improvement progress over time"""

    def __init__(self, tracking_file: Path):
        self.tracking_file = Path(tracking_file)
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """Load historical benchmarks"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {"benchmarks": []}

    def save_benchmark(self, benchmark: ModelBenchmark):
        """Save a benchmark to history"""
        self.history["benchmarks"].append(asdict(benchmark))

        with open(self.tracking_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_progress(self, model: str, metric: str = "overall_score") -> List[Tuple[str, float]]:
        """Get progress for a specific metric"""
        progress = []

        for benchmark in self.history["benchmarks"]:
            if benchmark["model"] == model:
                timestamp = benchmark["timestamp"]
                value = benchmark[metric]
                progress.append((timestamp, value))

        return sorted(progress, key=lambda x: x[0])

    def generate_progress_report(self, model: str) -> str:
        """Generate progress report"""
        progress = self.get_progress(model)

        if not progress:
            return f"No historical data for {model}"

        report = f"# Progress Report: {model}\n\n"
        report += f"Total Benchmarks: {len(progress)}\n\n"

        # Calculate trend
        if len(progress) >= 2:
            first_score = progress[0][1]
            last_score = progress[-1][1]
            improvement = last_score - first_score
            improvement_pct = (improvement / first_score) * 100 if first_score > 0 else 0

            report += f"First Score: {first_score:.3f}\n"
            report += f"Latest Score: {last_score:.3f}\n"
            report += f"Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)\n\n"

        report += "## Score History\n\n"
        report += "| Date | Score |\n"
        report += "|------|-------|\n"

        for timestamp, score in progress:
            date = timestamp.split('T')[0]
            report += f"| {date} | {score:.3f} |\n"

        return report


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Model Benchmarking System")
    parser.add_argument("--models", nargs="+", default=["codellama"], help="Models to benchmark")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--compare", action="store_true", help="Compare multiple models")
    parser.add_argument("--track", help="Track progress to file")
    parser.add_argument("--progress-report", help="Generate progress report for model")
    parser.add_argument("--output", help="Save results to JSON")

    args = parser.parse_args()

    benchmarker = ModelBenchmarker(ollama_url=args.ollama_url)

    if args.compare:
        # Compare models
        comparison = benchmarker.compare_models(args.models)

        if args.output:
            # Save comparison
            with open(args.output, 'w') as f:
                json.dump({
                    "comparison": comparison["comparison_table"],
                    "winner": comparison["winner"],
                    "benchmarks": [asdict(b) for b in comparison["benchmarks"]]
                }, f, indent=2)
            print(f"\n💾 Results saved to {args.output}")

    else:
        # Benchmark single model
        model = args.models[0] if args.models else "codellama"
        benchmark = benchmarker.benchmark_model(model)

        # Track progress if requested
        if args.track:
            tracker = ProgressTracker(args.track)
            tracker.save_benchmark(benchmark)
            print(f"\n💾 Progress tracked to {args.track}")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(asdict(benchmark), f, indent=2)
            print(f"\n💾 Results saved to {args.output}")

    # Generate progress report if requested
    if args.progress_report and args.track:
        tracker = ProgressTracker(args.track)
        report = tracker.generate_progress_report(args.progress_report)
        print(f"\n{report}")


if __name__ == "__main__":
    main()
