#!/usr/bin/env python3
"""
MASTER EXECUTION SCRIPT
Runs complete evaluation, benchmarking, and improvement pipeline
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """Run command and report results"""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False


def check_prerequisites():
    """Check if prerequisites are met"""
    print("\n" + "="*70)
    print("🔍 CHECKING PREREQUISITES")
    print("="*70)

    checks_passed = True

    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        checks_passed = False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check pytest
    result = subprocess.run(["pytest", "--version"], capture_output=True)
    if result.returncode == 0:
        print("✅ pytest installed")
    else:
        print("❌ pytest not installed (pip install pytest)")
        checks_passed = False

    # Check Ollama
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama running")
            models = response.json().get("models", [])
            print(f"   Available models: {len(models)}")
        else:
            print("❌ Ollama not responding")
            checks_passed = False
    except:
        print("❌ Ollama not running (start with: ollama serve)")
        checks_passed = False

    return checks_passed


def run_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("🧪 RUNNING TEST SUITES")
    print("="*70)

    test_files = [
        ("tests_real/test_security_real.py", "Security Tests"),
        ("tests_real/test_fixer_real.py", "Fixer Tests"),
        ("tests_real/test_analyzer_real.py", "Analyzer Tests"),
    ]

    results = []
    for test_file, description in test_files:
        if Path(test_file).exists():
            passed = run_command(f"pytest {test_file} -v -x", description)
            results.append((description, passed))
        else:
            print(f"⚠️  {test_file} not found, skipping")

    return results


def run_benchmarks():
    """Run performance benchmarks"""
    print("\n" + "="*70)
    print("⚡ RUNNING PERFORMANCE BENCHMARKS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_results_{timestamp}.json"

    passed = run_command(
        f"python3 benchmarking_real.py --models codellama --output {output_file} --track progress.json",
        "Benchmarking codellama"
    )

    return passed, output_file


def run_continuous_improvement():
    """Run continuous improvement analysis"""
    print("\n" + "="*70)
    print("🔄 RUNNING CONTINUOUS IMPROVEMENT")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"improvement_report_{timestamp}.md"
    json_file = f"improvement_data_{timestamp}.json"

    passed = run_command(
        f"python3 continuous_improvement_real.py --repo-path . --report {report_file} --json {json_file}",
        "Code Improvement Analysis"
    )

    return passed, report_file, json_file


def generate_summary_report(test_results, benchmark_results, improvement_results):
    """Generate comprehensive summary report"""
    print("\n" + "="*70)
    print("📊 GENERATING SUMMARY REPORT")
    print("="*70)

    report = f"""# Comprehensive Evaluation Report
Generated: {datetime.now().isoformat()}

## Executive Summary

### Test Results
"""

    total_tests = len(test_results)
    passed_tests = sum(1 for _, passed in test_results if passed)

    report += f"- Total Test Suites: {total_tests}\n"
    report += f"- Passed: {passed_tests}\n"
    report += f"- Failed: {total_tests - passed_tests}\n"
    report += f"- Pass Rate: {passed_tests/total_tests*100:.1f}%\n\n"

    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        report += f"- {test_name}: {status}\n"

    report += "\n### Benchmark Results\n"

    benchmark_passed, benchmark_file = benchmark_results
    if benchmark_passed and Path(benchmark_file).exists():
        try:
            with open(benchmark_file, 'r') as f:
                data = json.load(f)
                perf = data.get("performance", {})
                report += f"- Pass Rate: {perf.get('passed_tests', 0)/perf.get('total_tests', 1)*100:.1f}%\n"
                report += f"- Avg Response Time: {perf.get('avg_response_time', 0):.2f}s\n"
                report += f"- Quality Score: {perf.get('avg_quality_score', 0):.2f}/1.00\n"
        except:
            report += "- Benchmark data available in " + benchmark_file + "\n"
    else:
        report += "- ❌ Benchmark failed or file not found\n"

    report += "\n### Code Improvements\n"

    improvement_passed, improvement_report, improvement_json = improvement_results
    if improvement_passed and Path(improvement_json).exists():
        try:
            with open(improvement_json, 'r') as f:
                data = json.load(f)
                report += f"- Issues Found: {len(data.get('issues', []))}\n"
                report += f"- Improvements Suggested: {len(data.get('improvements', []))}\n"
        except:
            report += "- Improvement data available in " + improvement_report + "\n"
    else:
        report += "- ❌ Improvement analysis failed\n"

    report += "\n## Overall Assessment\n\n"

    overall_score = 0
    if passed_tests == total_tests:
        overall_score += 40
    elif passed_tests >= total_tests * 0.8:
        overall_score += 30

    if benchmark_passed:
        overall_score += 30

    if improvement_passed:
        overall_score += 30

    if overall_score >= 90:
        grade = "A - Excellent"
    elif overall_score >= 80:
        grade = "B - Good"
    elif overall_score >= 70:
        grade = "C - Satisfactory"
    else:
        grade = "D - Needs Improvement"

    report += f"**Overall Grade: {grade}**\n\n"
    report += f"**Score: {overall_score}/100**\n\n"

    report += "## Next Steps\n\n"

    if passed_tests < total_tests:
        report += "1. Fix failing tests before proceeding\n"

    if not benchmark_passed:
        report += "1. Review benchmark failures and optimize performance\n"

    if improvement_passed:
        report += f"1. Review improvement suggestions in `{improvement_report}`\n"
        report += "1. Implement high-priority improvements\n"

    report += "1. Re-run this evaluation after making changes\n"

    # Save report
    report_file = f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)

    print(report)
    print(f"\n💾 Report saved to {report_file}")

    return report_file


def main():
    """Main execution"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   COMPREHENSIVE EVALUATION & IMPROVEMENT SYSTEM                  ║
║   Real, Functioning Implementation                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix issues and try again.")
        return 1

    print("\n✅ All prerequisites met!\n")
    input("Press Enter to start evaluation...")

    # Run tests
    test_results = run_tests()

    # Run benchmarks
    benchmark_results = run_benchmarks()

    # Run continuous improvement
    improvement_results = run_continuous_improvement()

    # Generate summary
    report_file = generate_summary_report(test_results, benchmark_results, improvement_results)

    print("\n" + "="*70)
    print("🎉 EVALUATION COMPLETE")
    print("="*70)
    print(f"\n📄 Comprehensive report: {report_file}")
    print("\nKey Files:")
    print(f"  - Benchmark: {benchmark_results[1]}")
    print(f"  - Improvements: {improvement_results[1]}")
    print(f"  - Summary: {report_file}")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
