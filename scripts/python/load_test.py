#!/usr/bin/env python3
"""
Load Testing Agent - Enhanced Production Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stress tests endpoint with concurrent requests
Measures throughput, latency, and error rates
"""
import asyncio
import time
import sys
from typing import List, Dict
from datetime import datetime
from live_test_agent import call_vercel


async def concurrent_requests(
    num_requests: int,
    prompt: str,
    show_progress: bool = True
) -> tuple:
    """Execute multiple concurrent requests with progress tracking."""
    print(f'\n🚀 Starting {num_requests} concurrent requests...')
    print(f'📝 Prompt: {prompt[:50]}...' if len(prompt) > 50 else f'📝 Prompt: {prompt}')
    print('─' * 70 + '\n')

    tasks = []
    for i in range(num_requests):
        tasks.append(call_vercel(prompt))

    start_time = time.time()

    # Execute all requests
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.time() - start_time

    # Process results
    successful = []
    failed = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed.append({
                'index': i,
                'error': str(result),
                'error_type': type(result).__name__
            })
        else:
            provider, text, duration, metadata = result
            successful.append({
                'index': i,
                'provider': provider,
                'model': metadata.get('model', 'unknown'),
                'duration': duration,
                'response_length': len(text),
                'timestamp': metadata.get('timestamp')
            })

    # Generate detailed report
    generate_load_test_report(successful, failed, total_time, num_requests)

    return successful, failed


def generate_load_test_report(
    successful: List[Dict],
    failed: List[Dict],
    total_time: float,
    num_requests: int
):
    """Generate comprehensive load test report."""
    print('\n' + '╔' + '═' * 68 + '╗')
    print('║' + ' ' * 20 + '📊 LOAD TEST RESULTS' + ' ' * 27 + '║')
    print('╚' + '═' * 68 + '╝\n')

    # Overall metrics
    success_rate = (len(successful) / num_requests) * 100
    throughput = len(successful) / total_time if total_time > 0 else 0

    print(f'⏱️  Total Time: {total_time:.2f}s')
    print(f'✅ Successful: {len(successful)}/{num_requests} ({success_rate:.1f}%)')
    print(f'❌ Failed: {len(failed)}/{num_requests} ({(len(failed)/num_requests)*100:.1f}%)')
    print(f'🔥 Throughput: {throughput:.2f} requests/second')

    if successful:
        print('\n' + '─' * 70)
        print('⚡ LATENCY STATISTICS')
        print('─' * 70)

        latencies = [r['duration'] for r in successful]
        latencies_sorted = sorted(latencies)

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        median_latency = latencies_sorted[len(latencies) // 2]
        p95_latency = latencies_sorted[int(len(latencies) * 0.95)]
        p99_latency = latencies_sorted[int(len(latencies) * 0.99)]

        print(f'\n  Average:  {avg_latency:.3f}s')
        print(f'  Median:   {median_latency:.3f}s')
        print(f'  Min:      {min_latency:.3f}s')
        print(f'  Max:      {max_latency:.3f}s')
        print(f'  P95:      {p95_latency:.3f}s')
        print(f'  P99:      {p99_latency:.3f}s')

        # Latency distribution
        print(f'\n📊 Latency Distribution:')
        buckets = [
            ('< 1s', lambda x: x < 1.0),
            ('1-2s', lambda x: 1.0 <= x < 2.0),
            ('2-5s', lambda x: 2.0 <= x < 5.0),
            ('5-10s', lambda x: 5.0 <= x < 10.0),
            ('> 10s', lambda x: x >= 10.0)
        ]

        for label, condition in buckets:
            count = sum(1 for lat in latencies if condition(lat))
            percentage = (count / len(latencies)) * 100
            bar = '█' * int(percentage / 2)
            print(f'  {label:8s} {bar:25s} {count:3d} ({percentage:5.1f}%)')

        # Provider distribution
        providers = {}
        for r in successful:
            provider = r['provider']
            providers[provider] = providers.get(provider, 0) + 1

        print('\n' + '─' * 70)
        print('🔄 PROVIDER DISTRIBUTION')
        print('─' * 70)

        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(successful)) * 100
            bar = '█' * int(percentage / 2)

            # Calculate avg latency per provider
            provider_latencies = [r['duration'] for r in successful if r['provider'] == provider]
            avg_provider_latency = sum(provider_latencies) / len(provider_latencies)

            print(f'  {provider:12s} {bar:25s} {count:3d} ({percentage:5.1f}%) avg: {avg_provider_latency:.3f}s')

        # Response size statistics
        response_lengths = [r['response_length'] for r in successful]
        avg_response_length = sum(response_lengths) / len(response_lengths)

        print('\n' + '─' * 70)
        print('📏 RESPONSE STATISTICS')
        print('─' * 70)
        print(f'  Average Response Length: {avg_response_length:.0f} characters')
        print(f'  Min Response Length: {min(response_lengths)} characters')
        print(f'  Max Response Length: {max(response_lengths)} characters')

    if failed:
        print('\n' + '─' * 70)
        print('❌ ERROR ANALYSIS')
        print('─' * 70)

        # Group errors by type
        error_types = {}
        for f in failed:
            error_type = f.get('error_type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1

        print(f'\n  Error Types:')
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(failed)) * 100
            print(f'    {error_type:20s} {count:3d} ({percentage:5.1f}%)')

        # Show sample errors
        print(f'\n  Sample Errors (first 3):')
        for f in failed[:3]:
            error_msg = f["error"]
            if len(error_msg) > 60:
                error_msg = error_msg[:60] + '...'
            print(f'    Request #{f["index"]}: {error_msg}')

    # Performance rating
    print('\n' + '─' * 70)
    print('🎯 PERFORMANCE RATING')
    print('─' * 70)

    if success_rate >= 99:
        rating = '🏆 EXCELLENT'
    elif success_rate >= 95:
        rating = '✅ GOOD'
    elif success_rate >= 90:
        rating = '⚠️  ACCEPTABLE'
    else:
        rating = '❌ POOR'

    print(f'  Success Rate: {rating}')

    if successful:
        if avg_latency < 2.0:
            latency_rating = '🏆 EXCELLENT'
        elif avg_latency < 5.0:
            latency_rating = '✅ GOOD'
        elif avg_latency < 10.0:
            latency_rating = '⚠️  ACCEPTABLE'
        else:
            latency_rating = '❌ POOR'

        print(f'  Latency: {latency_rating}')

        if throughput > 5:
            throughput_rating = '🏆 EXCELLENT'
        elif throughput > 2:
            throughput_rating = '✅ GOOD'
        elif throughput > 1:
            throughput_rating = '⚠️  ACCEPTABLE'
        else:
            throughput_rating = '❌ POOR'

        print(f'  Throughput: {throughput_rating}')

    print('\n' + '═' * 70 + '\n')


async def ramp_up_test(
    max_concurrent: int = 20,
    step: int = 5,
    prompt: str = 'Quick test response'
):
    """Gradually increase load to find system limits."""
    print('\n╔' + '═' * 68 + '╗')
    print('║' + ' ' * 18 + '📈 RAMP-UP LOAD TEST' + ' ' * 29 + '║')
    print('╚' + '═' * 68 + '╝\n')

    print(f'🎯 Testing from {step} to {max_concurrent} concurrent requests')
    print(f'📝 Prompt: {prompt[:50]}...' if len(prompt) > 50 else f'📝 Prompt: {prompt}')
    print('─' * 70 + '\n')

    results = {}

    for concurrent in range(step, max_concurrent + 1, step):
        print(f'\n{"="*70}')
        print(f'🔄 Testing with {concurrent} concurrent requests')
        print(f'{"="*70}')

        successful, failed = await concurrent_requests(concurrent, prompt, show_progress=False)

        success_rate = (len(successful) / concurrent) * 100
        avg_latency = sum(r['duration'] for r in successful) / len(successful) if successful else 0

        results[concurrent] = {
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': success_rate,
            'avg_latency': avg_latency
        }

        print(f'\n  ✅ Success Rate: {success_rate:.1f}%')
        print(f'  ⚡ Avg Latency: {avg_latency:.3f}s')

        # Stop if performance degrades significantly
        if success_rate < 80:
            print(f'\n⚠️  Performance degradation detected at {concurrent} concurrent requests')
            print(f'   Stopping ramp-up test')
            break

        # Cool-down between tests
        if concurrent < max_concurrent:
            cooldown = 3
            print(f'\n⏳ Cooling down for {cooldown}s...')
            await asyncio.sleep(cooldown)

    # Generate summary
    print('\n' + '╔' + '═' * 68 + '╗')
    print('║' + ' ' * 18 + '📊 RAMP-UP SUMMARY' + ' ' * 31 + '║')
    print('╚' + '═' * 68 + '╝\n')

    print(f'{"Concurrent":>12s} {"Success Rate":>15s} {"Avg Latency":>15s} {"Rating":>15s}')
    print('─' * 70)

    for concurrent, data in sorted(results.items()):
        success_rate = data['success_rate']
        avg_latency = data['avg_latency']

        if success_rate >= 95 and avg_latency < 5.0:
            rating = '🏆 Excellent'
        elif success_rate >= 90 and avg_latency < 10.0:
            rating = '✅ Good'
        elif success_rate >= 80:
            rating = '⚠️  Acceptable'
        else:
            rating = '❌ Poor'

        print(f'{concurrent:>12d} {success_rate:>14.1f}% {avg_latency:>14.3f}s {rating:>15s}')

    print('─' * 70)

    # Find optimal concurrency
    optimal = max(
        [(c, d) for c, d in results.items() if d['success_rate'] >= 95],
        key=lambda x: x[0],
        default=(0, None)
    )

    if optimal[1]:
        print(f'\n💡 Recommended max concurrency: {optimal[0]} requests')
        print(f'   (Success rate: {optimal[1]["success_rate"]:.1f}%, Avg latency: {optimal[1]["avg_latency"]:.3f}s)')

    print('\n' + '═' * 70 + '\n')


async def sustained_load_test(
    concurrent: int = 10,
    duration_seconds: int = 60,
    prompt: str = 'Sustained load test'
):
    """Run sustained load for specified duration."""
    print('\n╔' + '═' * 68 + '╗')
    print('║' + ' ' * 16 + '⏱️  SUSTAINED LOAD TEST' + ' ' * 28 + '║')
    print('╚' + '═' * 68 + '╝\n')

    print(f'🎯 Running {concurrent} concurrent requests for {duration_seconds}s')
    print(f'📝 Prompt: {prompt[:50]}...' if len(prompt) > 50 else f'📝 Prompt: {prompt}')
    print('─' * 70 + '\n')

    start_time = time.time()
    end_time = start_time + duration_seconds

    all_results = []
    iteration = 0

    while time.time() < end_time:
        iteration += 1
        elapsed = time.time() - start_time
        remaining = duration_seconds - elapsed

        print(f'\n🔄 Iteration {iteration} (elapsed: {elapsed:.1f}s, remaining: {remaining:.1f}s)')

        successful, failed = await concurrent_requests(concurrent, prompt, show_progress=False)
        all_results.extend(successful)

        # Brief pause between iterations
        if time.time() < end_time:
            await asyncio.sleep(1)

    total_time = time.time() - start_time

    # Generate sustained load report
    print('\n' + '╔' + '═' * 68 + '╗')
    print('║' + ' ' * 15 + '📊 SUSTAINED LOAD RESULTS' + ' ' * 26 + '║')
    print('╚' + '═' * 68 + '╝\n')

    print(f'⏱️  Total Duration: {total_time:.2f}s')
    print(f'📊 Total Requests: {len(all_results)}')
    print(f'🔥 Average Throughput: {len(all_results)/total_time:.2f} requests/second')

    if all_results:
        latencies = [r['duration'] for r in all_results]
        print(f'\n⚡ Latency Statistics:')
        print(f'  Average: {sum(latencies)/len(latencies):.3f}s')
        print(f'  Min: {min(latencies):.3f}s')
        print(f'  Max: {max(latencies):.3f}s')

        # Provider distribution
        providers = {}
        for r in all_results:
            provider = r['provider']
            providers[provider] = providers.get(provider, 0) + 1

        print(f'\n🔄 Provider Distribution:')
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(all_results)) * 100
            print(f'  {provider:12s} {count:4d} ({percentage:5.1f}%)')

    print('\n' + '═' * 70 + '\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python3 load_test.py burst <num_requests> [prompt]')
        print('  python3 load_test.py ramp <max_concurrent> [step]')
        print('  python3 load_test.py sustained <concurrent> <duration_seconds> [prompt]')
        print('\nExamples:')
        print('  python3 load_test.py burst 10')
        print('  python3 load_test.py ramp 20 5')
        print('  python3 load_test.py sustained 5 60')
        sys.exit(1)

    mode = sys.argv[1]

    try:
        if mode == 'burst':
            num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            prompt = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else 'Load test query'
            asyncio.run(concurrent_requests(num_requests, prompt))

        elif mode == 'ramp':
            max_concurrent = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            step = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            prompt = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else 'Ramp test query'
            asyncio.run(ramp_up_test(max_concurrent, step, prompt))

        elif mode == 'sustained':
            concurrent = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
            prompt = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else 'Sustained test query'
            asyncio.run(sustained_load_test(concurrent, duration, prompt))

        else:
            print(f'❌ Unknown mode: {mode}')
            print('Valid modes: burst, ramp, sustained')
            sys.exit(1)

    except KeyboardInterrupt:
        print('\n\n⚠️  Load test interrupted by user')
        sys.exit(130)
    except ValueError as e:
        print(f'❌ Invalid argument: {e}')
        sys.exit(1)
