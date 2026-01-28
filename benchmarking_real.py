#!/usr/bin/env python3
"""
REAL Benchmarking System - Actually Measures Performance
Tests different models and tracks metrics over time
"""

import json
import time
import statistics
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests


@dataclass
class BenchmarkMetrics:
    """Real performance metrics"""
    model: str
    test_name: str
    response_time: float
    success: bool
    quality_score: float  # 0-1
    tokens_generated: int
    memory_usage_mb: float
    timestamp: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ModelPerformance:
    """Aggregated performance for a model"""
    model: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_response_time: float
    p95_response_time: float
    avg_quality_score: float
    total_tokens: int
    avg_memory_mb: float
    timestamp: str

    def pass_rate(self) -> float:
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0.0

    def to_dict(self):
        return asdict(self)


class OllamaBenchmarker:
    """Real benchmarking that actually tests performance"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"

    def query_timed(self, model: str, prompt: str, temperature: float = 0.2) -> Tuple[str, float, int]:
        """Query with timing and token counting"""
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
            result_json = response.json()
            result_text = result_json.get("response", "")

            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            tokens = len(result_text) // 4

            return result_text, elapsed, tokens

        except Exception as e:
            elapsed = time.time() - start_time
            return f"Error: {e}", elapsed, 0

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def evaluate_code_quality(self, code: str, expected_elements: List[str]) -> float:
        """Evaluate generated code quality"""
        if not code or code.startswith("Error:"):
            return 0.0

        score = 0.0

        # Check expected elements
        elements_present = sum(1 for elem in expected_elements if elem.lower() in code.lower())
        score += (elements_present / len(expected_elements)) * 0.5

        # Check code structure
        has_function = "def " in code
        has_class = "class " in code
        has_docstring = '"""' in code or "'''" in code
        has_typing = ":" in code and "->" in code

        structure_score = sum([has_function or has_class, has_docstring]) / 2
        score += structure_score * 0.3

        # Check length (not too short, not too long)
        length_score = 1.0 if 50 < len(code) < 5000 else 0.5
        score += length_score * 0.2

        return min(score, 1.0)

    def run_code_generation_test(self, model: str, test_name: str, prompt: str, expected: List[str]) -> BenchmarkMetrics:
        """Run a single code generation test"""
        mem_before = self.get_memory_usage()

        response, elapsed, tokens = self.query_timed(model, prompt)

        mem_after = self.get_memory_usage()
        mem_used = mem_after - mem_before

        quality = self.evaluate_code_quality(response, expected)
        success = quality >= 0.6 and elapsed < 30.0

        return BenchmarkMetrics(
            model=model,
            test_name=test_name,
            response_time=elapsed,
            success=success,
            quality_score=quality,
            tokens_generated=tokens,
            memory_usage_mb=mem_used,
            timestamp=datetime.utcnow().isoformat()
        )

    def run_error_analysis_test(self, model: str, test_name: str, error: str) -> BenchmarkMetrics:
        """Run error analysis test"""
        prompt = f"Analyze this error and suggest a fix in 2-3 sentences: {error}"

        mem_before = self.get_memory_usage()
        response, elapsed, tokens = self.query_timed(model, prompt)
        mem_after = self.get_memory_usage()

        # Quality: Should mention key terms
        quality = 0.0
        if "fix" in response.lower() or "solution" in response.lower():
            quality += 0.5
        if len(response) > 20:
            quality += 0.3
        if elapsed < 15.0:
            quality += 0.2

        success = quality >= 0.5 and elapsed < 30.0

        return BenchmarkMetrics(
            model=model,
            test_name=test_name,
            response_time=elapsed,
            success=success,
            quality_score=quality,
            tokens_generated=tokens,
            memory_usage_mb=mem_after - mem_before,
            timestamp=datetime.utcnow().isoformat()
        )

    def run_benchmark_suite(self, model: str) -> List[BenchmarkMetrics]:
        """Run complete benchmark suite"""
        print(f"\n{'='*70}")
        print(f"Benchmarking: {model}")
        print(f"{'='*70}\n")

        metrics = []

        # Test 1: Simple function
        print("Test 1: Simple Function Generation...", end=" ")
        m = self.run_code_generation_test(
            model,
            "simple_function",
            "Create a Python function called add_numbers that takes two parameters and returns their sum. Only code, no explanations.",
            ["def add_numbers", "return", "+"]
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 2: Class creation
        print("Test 2: Class Generation...", end=" ")
        m = self.run_code_generation_test(
            model,
            "class_creation",
            "Create a Python class Person with __init__ taking name and age. Only code.",
            ["class Person", "__init__", "self", "name", "age"]
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 3: Error handling
        print("Test 3: Error Handling Code...", end=" ")
        m = self.run_code_generation_test(
            model,
            "error_handling",
            "Create a function that reads a file with try/except. Only code.",
            ["def", "try", "except", "open", "with"]
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 4: Import error analysis
        print("Test 4: Import Error Analysis...", end=" ")
        m = self.run_error_analysis_test(
            model,
            "import_error_analysis",
            "ImportError: No module named 'requests'"
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 5: Syntax error analysis
        print("Test 5: Syntax Error Analysis...", end=" ")
        m = self.run_error_analysis_test(
            model,
            "syntax_error_analysis",
            "SyntaxError: invalid syntax at line 10"
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 6: File not found analysis
        print("Test 6: File Error Analysis...", end=" ")
        m = self.run_error_analysis_test(
            model,
            "file_error_analysis",
            'Error: File "config.py" not found'
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 7: List comprehension
        print("Test 7: List Comprehension...", end=" ")
        m = self.run_code_generation_test(
            model,
            "list_comprehension",
            "Create a Python function that uses list comprehension to filter even numbers. Only code.",
            ["def", "return", "[", "for", "if", "%"]
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        # Test 8: Decorator
        print("Test 8: Decorator Creation...", end=" ")
        m = self.run_code_generation_test(
            model,
            "decorator",
            "Create a simple Python decorator that prints function name. Only code.",
            ["def", "def", "return", "functools"]
        )
        metrics.append(m)
        print(f"{'✓' if m.success else '✗'} ({m.response_time:.2f}s, Q:{m.quality_score:.2f})")

        return metrics

    def calculate_performance(self, metrics: List[BenchmarkMetrics]) -> ModelPerformance:
        """Calculate aggregate performance"""
        if not metrics:
            return ModelPerformance(
                model="unknown",
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                avg_response_time=0.0,
                p95_response_time=0.0,
                avg_quality_score=0.0,
                total_tokens=0,
                avg_memory_mb=0.0,
                timestamp=datetime.utcnow().isoformat()
            )

        response_times = [m.response_time for m in metrics]
        quality_scores = [m.quality_score for m in metrics]

        return ModelPerformance(
            model=metrics[0].model,
            total_tests=len(metrics),
            passed_tests=sum(1 for m in metrics if m.success),
            failed_tests=sum(1 for m in metrics if not m.success),
            avg_response_time=statistics.mean(response_times),
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0],
            avg_quality_score=statistics.mean(quality_scores),
            total_tokens=sum(m.tokens_generated for m in metrics),
            avg_memory_mb=statistics.mean(m.memory_usage_mb for m in metrics),
            timestamp=datetime.utcnow().isoformat()
        )

    def print_performance_summary(self, perf: ModelPerformance):
        """Print performance summary"""
        print(f"\n{'='*70}")
        print(f"Performance Summary: {perf.model}")
        print(f"{'='*70}")
        print(f"Tests: {perf.total_tests} total, {perf.passed_tests} passed, {perf.failed_tests} failed")
        print(f"Pass Rate: {perf.pass_rate()*100:.1f}%")
        print(f"Response Time: {perf.avg_response_time:.2f}s avg, {perf.p95_response_time:.2f}s P95")
        print(f"Quality Score: {perf.avg_quality_score:.2f}/1.00")
        print(f"Tokens: {perf.total_tokens} total, {perf.total_tokens/perf.total_tests:.0f} avg/test")
        print(f"Memory: {perf.avg_memory_mb:.1f} MB avg")

        # Grade
        grade = "F"
        if perf.pass_rate() >= 0.9 and perf.avg_quality_score >= 0.8:
            grade = "A"
        elif perf.pass_rate() >= 0.8 and perf.avg_quality_score >= 0.7:
            grade = "B"
        elif perf.pass_rate() >= 0.7:
            grade = "C"
        elif perf.pass_rate() >= 0.6:
            grade = "D"

        print(f"Grade: {grade}")
        print(f"{'='*70}")

    def compare_models(self, models: List[str]) -> Dict:
        """Compare multiple models"""
        print(f"\n{'='*70}")
        print(f"COMPARING {len(models)} MODELS")
        print(f"{'='*70}\n")

        results = {}

        for model in models:
            try:
                metrics = self.run_benchmark_suite(model)
                perf = self.calculate_performance(metrics)
                self.print_performance_summary(perf)
                results[model] = {
                    "metrics": metrics,
                    "performance": perf
                }
            except Exception as e:
                print(f"\n❌ Error benchmarking {model}: {e}\n")

        if len(results) > 1:
            self.print_comparison_table(results)

        return results

    def print_comparison_table(self, results: Dict):
        """Print comparison table"""
        print(f"\n{'='*70}")
        print("COMPARISON TABLE")
        print(f"{'='*70}\n")

        # Sort by pass rate
        sorted_models = sorted(
            results.items(),
            key=lambda x: x[1]["performance"].pass_rate(),
            reverse=True
        )

        print(f"{'Model':<20} {'Pass Rate':<12} {'Avg Time':<12} {'Quality':<10} {'Grade'}")
        print(f"{'-'*70}")

        for model, data in sorted_models:
            perf = data["performance"]
            grade = "A" if perf.pass_rate() >= 0.9 else "B" if perf.pass_rate() >= 0.8 else "C"

            winner = "🏆" if model == sorted_models[0][0] else "  "

            print(f"{model:<20} {perf.pass_rate()*100:>5.1f}%    {perf.avg_response_time:>6.2f}s    {perf.avg_quality_score:>5.2f}/1.0  {grade}  {winner}")

        print(f"{'='*70}")


class ProgressTracker:
    """Track performance over time"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db = self._load_db()

    def _load_db(self) -> Dict:
        """Load history database"""
        if self.db_path.exists():
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {"benchmarks": []}

    def _save_db(self):
        """Save history database"""
        with open(self.db_path, 'w') as f:
            json.dump(self.db, f, indent=2)

    def add_benchmark(self, perf: ModelPerformance):
        """Add benchmark result"""
        self.db["benchmarks"].append(perf.to_dict())
        self._save_db()

    def get_history(self, model: str) -> List[ModelPerformance]:
        """Get history for model"""
        history = []
        for b in self.db["benchmarks"]:
            if b["model"] == model:
                history.append(ModelPerformance(**b))
        return sorted(history, key=lambda x: x.timestamp)

    def print_progress_report(self, model: str):
        """Print progress report"""
        history = self.get_history(model)

        if not history:
            print(f"No history for {model}")
            return

        print(f"\n{'='*70}")
        print(f"Progress Report: {model}")
        print(f"{'='*70}\n")
        print(f"Total Benchmarks: {len(history)}")

        if len(history) >= 2:
            first = history[0]
            latest = history[-1]

            pass_rate_change = (latest.pass_rate() - first.pass_rate()) * 100
            time_change = latest.avg_response_time - first.avg_response_time
            quality_change = latest.avg_quality_score - first.avg_quality_score

            print(f"\nFirst Benchmark: {first.timestamp[:10]}")
            print(f"Latest Benchmark: {latest.timestamp[:10]}")
            print(f"\nChanges:")
            print(f"  Pass Rate: {first.pass_rate()*100:.1f}% → {latest.pass_rate()*100:.1f}% ({pass_rate_change:+.1f}%)")
            print(f"  Avg Time: {first.avg_response_time:.2f}s → {latest.avg_response_time:.2f}s ({time_change:+.2f}s)")
            print(f"  Quality: {first.avg_quality_score:.2f} → {latest.avg_quality_score:.2f} ({quality_change:+.2f})")

        print(f"\n{'Date':<12} {'Pass Rate':<12} {'Avg Time':<12} {'Quality'}")
        print(f"{'-'*50}")
        for h in history[-10:]:  # Last 10
            print(f"{h.timestamp[:10]:<12} {h.pass_rate()*100:>5.1f}%    {h.avg_response_time:>6.2f}s    {h.avg_quality_score:>5.2f}")

        print(f"{'='*70}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Real Benchmarking System")
    parser.add_argument("--models", nargs="+", default=["codellama"], help="Models to benchmark")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--compare", action="store_true", help="Compare models")
    parser.add_argument("--track", help="Track progress (path to DB)")
    parser.add_argument("--progress-report", help="Show progress for model")
    parser.add_argument("--output", help="Save results to JSON")

    args = parser.parse_args()

    # Check Ollama connection
    try:
        response = requests.get(f"{args.ollama_url}/api/tags", timeout=5)
        response.raise_for_status()
    except:
        print(f"❌ Cannot connect to Ollama at {args.ollama_url}")
        print("   Please ensure Ollama is running: ollama serve")
        return 1

    benchmarker = OllamaBenchmarker(ollama_url=args.ollama_url)

    # Progress report
    if args.progress_report and args.track:
        tracker = ProgressTracker(Path(args.track))
        tracker.print_progress_report(args.progress_report)
        return 0

    # Compare models
    if args.compare:
        results = benchmarker.compare_models(args.models)

        if args.output:
            output_data = {}
            for model, data in results.items():
                output_data[model] = {
                    "performance": data["performance"].to_dict(),
                    "metrics": [m.to_dict() for m in data["metrics"]]
                }

            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n💾 Results saved to {args.output}")

        # Track if requested
        if args.track:
            tracker = ProgressTracker(Path(args.track))
            for model, data in results.items():
                tracker.add_benchmark(data["performance"])
            print(f"💾 Progress tracked to {args.track}")

    # Single model benchmark
    else:
        model = args.models[0]
        metrics = benchmarker.run_benchmark_suite(model)
        perf = benchmarker.calculate_performance(metrics)
        benchmarker.print_performance_summary(perf)

        if args.track:
            tracker = ProgressTracker(Path(args.track))
            tracker.add_benchmark(perf)
            print(f"\n💾 Progress tracked to {args.track}")

        if args.output:
            output_data = {
                "performance": perf.to_dict(),
                "metrics": [m.to_dict() for m in metrics]
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"💾 Results saved to {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
