#!/usr/bin/env python3
"""
Comprehensive Test Suite - Enhanced Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tests multiple scenarios and validates system behavior
"""
import asyncio
import sys
import time
from datetime import datetime
from live_test_agent import call_vercel, print_result

TEST_CASES = [
    {
        'name': 'Simple Query',
        'prompt': 'What is 2+2?',
        'expected_latency': 2.0,
        'category': 'basic'
    },
    {
        'name': 'Complex Reasoning',
        'prompt': 'Explain the difference between supervised and unsupervised learning in detail',
        'expected_latency': 5.0,
        'category': 'reasoning'
    },
    {
        'name': 'Current Events',
        'prompt': 'What are the latest developments in AI announced this week?',
        'expected_latency': 4.0,
        'category': 'knowledge'
    },
    {
        'name': 'Code Generation',
        'prompt': 'Write a Python function to calculate fibonacci numbers with memoization',
        'expected_latency': 3.0,
        'category': 'code'
    },
    {
        'name': 'Long Context',
        'prompt': 'Summarize the key architectural differences between transformer models and RNNs, including attention mechanisms',
        'expected_latency': 6.0,
        'category': 'reasoning'
    },
    {
        'name': 'Multi-step Problem',
        'prompt': 'If a train travels 120 km in 2 hours, then increases speed by 20%, how far will it travel in the next 3 hours?',
        'expected_latency': 3.0,
        'category': 'math'
    },
    {
        'name': 'Creative Writing',
        'prompt': 'Write a haiku about artificial intelligence',
        'expected_latency': 2.0,
        'category': 'creative'
    },
    {
        'name': 'Technical Explanation',
        'prompt': 'Explain how gradient descent works in neural network training',
        'expected_latency': 4.0,
        'category': 'technical'
    }
]


async def run_test_case(test: dict, index: int, total: int) -> dict:
    """Run a single test case with detailed reporting."""
    print(f'\n{"="*70}')
    print(f'Test {index}/{total}: {test["name"]} [{test["category"]}]')
    print(f'{"="*70}')
    print(f'📝 Prompt: {test["prompt"][:60]}...' if len(test["prompt"]) > 60 else f'📝 Prompt: {test["prompt"]}')

    try:
        provider, text, duration, metadata = await call_vercel(test['prompt'])
        print_result(provider, text, duration, metadata)

        # Validate latency
        latency_ok = duration <= test['expected_latency']
        if not latency_ok:
            print(f'⚠️  Latency warning: {duration:.2f}s > {test["expected_latency"]}s')
        else:
            print(f'✅ Latency acceptable: {duration:.2f}s ≤ {test["expected_latency"]}s')

        # Validate response quality
        response_ok = len(text) > 10  # Basic sanity check
        if not response_ok:
            print(f'⚠️  Response too short: {len(text)} chars')

        return {
            'name': test['name'],
            'category': test['category'],
            'provider': provider,
            'model': metadata.get('model', 'unknown'),
            'duration': duration,
            'expected_latency': test['expected_latency'],
            'latency_ok': latency_ok,
            'response_length': len(text),
            'response_ok': response_ok,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f'❌ Test failed: {e}')
        return {
            'name': test['name'],
            'category': test['category'],
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


async def run_all_tests(rate_limit_delay: int = 2):
    """Execute all test cases and generate comprehensive report."""
    print('╔' + '═' * 68 + '╗')
    print('║' + ' ' * 15 + '🧪 COMPREHENSIVE TEST SUITE' + ' ' * 25 + '║')
    print('╚' + '═' * 68 + '╝\n')

    start_time = time.time()
    results = []

    for i, test in enumerate(TEST_CASES, 1):
        result = await run_test_case(test, i, len(TEST_CASES))
        results.append(result)

        # Rate limiting between tests
        if i < len(TEST_CASES):
            print(f'\n⏳ Waiting {rate_limit_delay}s before next test...')
            await asyncio.sleep(rate_limit_delay)

    total_time = time.time() - start_time

    # Generate comprehensive report
    generate_report(results, total_time)

    # Return success status
    failed = [r for r in results if not r['success']]
    return len(failed) == 0


def generate_report(results: list, total_time: float):
    """Generate detailed test report."""
    print('\n' + '╔' + '═' * 68 + '╗')
    print('║' + ' ' * 20 + '📊 TEST SUMMARY REPORT' + ' ' * 25 + '║')
    print('╚' + '═' * 68 + '╝\n')

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    # Overall statistics
    print(f'⏱️  Total Execution Time: {total_time:.2f}s')
    print(f'✅ Passed: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)')
    print(f'❌ Failed: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)')

    if successful:
        print('\n' + '─' * 70)
        print('📈 PERFORMANCE METRICS')
        print('─' * 70)

        # Latency statistics
        latencies = [r['duration'] for r in successful]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        median_latency = sorted(latencies)[len(latencies) // 2]

        print(f'\n⚡ Latency Statistics:')
        print(f'  Average: {avg_latency:.3f}s')
        print(f'  Median:  {median_latency:.3f}s')
        print(f'  Min:     {min_latency:.3f}s')
        print(f'  Max:     {max_latency:.3f}s')

        # Latency compliance
        latency_compliant = [r for r in successful if r.get('latency_ok', False)]
        print(f'\n✅ Latency Compliance: {len(latency_compliant)}/{len(successful)} tests within expected limits')

        # Provider distribution
        providers = {}
        for r in successful:
            provider = r['provider']
            providers[provider] = providers.get(provider, 0) + 1

        print(f'\n🔄 Provider Distribution:')
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(successful)) * 100
            bar = '█' * int(percentage / 5)
            print(f'  {provider:12s} {bar:20s} {count:2d} ({percentage:5.1f}%)')

        # Model distribution
        models = {}
        for r in successful:
            model = r.get('model', 'unknown')
            models[model] = models.get(model, 0) + 1

        if len(models) > 1:
            print(f'\n🎯 Model Distribution:')
            for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(successful)) * 100
                print(f'  {model:30s} {count:2d} ({percentage:5.1f}%)')

        # Category performance
        categories = {}
        for r in successful:
            cat = r.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r['duration'])

        print(f'\n📊 Performance by Category:')
        for cat, durations in sorted(categories.items()):
            avg = sum(durations) / len(durations)
            print(f'  {cat:12s} avg: {avg:.3f}s  (n={len(durations)})')

        # Response quality
        avg_response_length = sum(r['response_length'] for r in successful) / len(successful)
        print(f'\n📏 Average Response Length: {avg_response_length:.0f} characters')

    if failed:
        print('\n' + '─' * 70)
        print('❌ FAILED TESTS')
        print('─' * 70)
        for r in failed:
            print(f'\n  Test: {r["name"]}')
            print(f'  Category: {r.get("category", "N/A")}')
            print(f'  Error: {r.get("error", "Unknown error")}')
            print(f'  Timestamp: {r.get("timestamp", "N/A")}')

    # Recommendations
    print('\n' + '─' * 70)
    print('💡 RECOMMENDATIONS')
    print('─' * 70)

    if successful:
        if avg_latency > 5.0:
            print('  ⚠️  High average latency detected - consider optimizing provider selection')
        elif avg_latency < 2.0:
            print('  ✅ Excellent average latency - system performing optimally')
        else:
            print('  ✅ Good average latency - system performing well')

        # Provider diversity check
        if len(providers) == 1:
            print('  ⚠️  Only one provider used - verify fallback chain is working')
        else:
            print(f'  ✅ Good provider diversity - {len(providers)} providers utilized')

    if failed:
        print(f'  ❌ {len(failed)} test(s) failed - investigate error logs')

    print('\n' + '═' * 70 + '\n')


if __name__ == '__main__':
    try:
        rate_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 2
        success = asyncio.run(run_all_tests(rate_limit))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print('\n\n⚠️  Test suite interrupted by user')
        sys.exit(130)
