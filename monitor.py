#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard - Enhanced Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Continuously monitors endpoint with live statistics
"""
import asyncio
import time
import sys
import os
from datetime import datetime
from collections import deque
from live_test_agent import call_vercel


class LiveMonitor:
    """Real-time monitoring with rolling statistics and alerts."""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.latencies = deque(maxlen=window_size)
        self.providers = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.errors = 0
        self.total_requests = 0
        self.start_time = time.time()
        self.last_error_time = None

    def record(self, provider: str, duration: float):
        """Record a successful request."""
        self.latencies.append(duration)
        self.providers.append(provider)
        self.timestamps.append(time.time())
        self.total_requests += 1

    def record_error(self, error: str):
        """Record a failed request."""
        self.errors += 1
        self.total_requests += 1
        self.last_error_time = time.time()

    def get_stats(self) -> dict:
        """Calculate current statistics."""
        if not self.latencies:
            return {
                'avg_latency': 0,
                'min_latency': 0,
                'max_latency': 0,
                'p95_latency': 0,
                'success_rate': 0,
                'primary_provider': 'N/A',
                'requests_per_second': 0,
                'uptime': time.time() - self.start_time
            }

        latencies_list = list(self.latencies)
        providers_list = list(self.providers)
        timestamps_list = list(self.timestamps)

        # Latency stats
        latencies_sorted = sorted(latencies_list)
        p95_index = int(len(latencies_sorted) * 0.95)

        # Provider distribution
        provider_counts = {}
        for p in providers_list:
            provider_counts[p] = provider_counts.get(p, 0) + 1

        primary_provider = max(provider_counts.items(), key=lambda x: x[1])[0] if provider_counts else 'N/A'

        # Calculate requests per second
        if len(timestamps_list) > 1:
            time_span = timestamps_list[-1] - timestamps_list[0]
            requests_per_second = len(timestamps_list) / time_span if time_span > 0 else 0
        else:
            requests_per_second = 0

        return {
            'avg_latency': sum(latencies_list) / len(latencies_list),
            'min_latency': min(latencies_list),
            'max_latency': max(latencies_list),
            'p95_latency': latencies_sorted[p95_index] if p95_index < len(latencies_sorted) else latencies_sorted[-1],
            'success_rate': ((self.total_requests - self.errors) / self.total_requests * 100) if self.total_requests > 0 else 0,
            'primary_provider': primary_provider,
            'provider_distribution': provider_counts,
            'requests_per_second': requests_per_second,
            'uptime': time.time() - self.start_time
        }

    def get_alerts(self, stats: dict) -> list:
        """Check for alert conditions."""
        alerts = []

        # High latency alert
        if stats['avg_latency'] > 10.0:
            alerts.append('🚨 HIGH LATENCY: Average > 10s')
        elif stats['avg_latency'] > 5.0:
            alerts.append('⚠️  ELEVATED LATENCY: Average > 5s')

        # Low success rate alert
        if stats['success_rate'] < 80:
            alerts.append('🚨 LOW SUCCESS RATE: < 80%')
        elif stats['success_rate'] < 95:
            alerts.append('⚠️  DEGRADED SUCCESS RATE: < 95%')

        # Recent error alert
        if self.last_error_time and (time.time() - self.last_error_time) < 30:
            alerts.append('⚠️  RECENT ERROR: Within last 30s')

        # Single provider alert
        if len(stats.get('provider_distribution', {})) == 1 and self.total_requests > 5:
            alerts.append('⚠️  SINGLE PROVIDER: Fallback may not be working')

        return alerts

    def display_stats(self):
        """Display formatted statistics dashboard."""
        # Clear screen
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            print('\033[2J\033[H', end='')

        stats = self.get_stats()
        alerts = self.get_alerts(stats)

        # Header
        print('╔' + '═' * 68 + '╗')
        print('║' + ' ' * 15 + '🔍 LIVE MONITORING DASHBOARD' + ' ' * 23 + '║')
        print('║' + ' ' * 20 + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}' + ' ' * 27 + '║')
        print('╚' + '═' * 68 + '╝\n')

        # Alerts section
        if alerts:
            print('🚨 ALERTS')
            print('─' * 70)
            for alert in alerts:
                print(f'  {alert}')
            print()

        # System status
        print('📊 SYSTEM STATUS')
        print('─' * 70)
        print(f'  Uptime: {stats["uptime"]:.0f}s')
        print(f'  Total Requests: {self.total_requests}')
        print(f'  Success Rate: {stats["success_rate"]:.1f}%')
        print(f'  Errors: {self.errors}')
        print(f'  Throughput: {stats["requests_per_second"]:.2f} req/s')

        # Latency metrics
        print(f'\n⚡ LATENCY (last {len(self.latencies)} requests)')
        print('─' * 70)
        print(f'  Average: {stats["avg_latency"]:.3f}s')
        print(f'  Min:     {stats["min_latency"]:.3f}s')
        print(f'  Max:     {stats["max_latency"]:.3f}s')
        print(f'  P95:     {stats["p95_latency"]:.3f}s')

        # Visual latency graph
        if self.latencies:
            print(f'\n  Recent Latency Trend:')
            max_lat = max(self.latencies)
            for i, lat in enumerate(list(self.latencies)[-10:]):  # Last 10 requests
                bar_length = int((lat / max_lat) * 30) if max_lat > 0 else 0
                bar = '█' * bar_length
                print(f'    {i+1:2d}. {bar} {lat:.3f}s')

        # Provider distribution
        print(f'\n🤖 PROVIDERS')
        print('─' * 70)
        print(f'  Primary: {stats["primary_provider"]}')

        if stats.get('provider_distribution'):
            print(f'\n  Distribution:')
            for provider, count in sorted(stats['provider_distribution'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.providers)) * 100
                bar = '█' * int(percentage / 3)
                print(f'    {provider:12s} {bar:25s} {count:3d} ({percentage:5.1f}%)')

        # Performance rating
        print(f'\n🎯 PERFORMANCE RATING')
        print('─' * 70)

        if stats['success_rate'] >= 99 and stats['avg_latency'] < 3.0:
            rating = '🏆 EXCELLENT'
            color = '\033[92m'  # Green
        elif stats['success_rate'] >= 95 and stats['avg_latency'] < 5.0:
            rating = '✅ GOOD'
            color = '\033[92m'  # Green
        elif stats['success_rate'] >= 90 and stats['avg_latency'] < 10.0:
            rating = '⚠️  ACCEPTABLE'
            color = '\033[93m'  # Yellow
        else:
            rating = '❌ POOR'
            color = '\033[91m'  # Red

        reset = '\033[0m'
        print(f'  Overall: {color}{rating}{reset}')

        # Footer
        print('\n' + '═' * 70)
        print('Press Ctrl+C to stop monitoring')
        print('═' * 70)


async def monitor_loop(
    interval: int = 5,
    test_prompts: list = None,
    rotate_prompts: bool = True
):
    """Continuously monitor endpoint with configurable prompts."""
    monitor = LiveMonitor()

    if test_prompts is None:
        test_prompts = [
            'What is artificial intelligence?',
            'Explain machine learning',
            'What is deep learning?',
            'Define neural networks',
            'What is natural language processing?',
            'Explain computer vision',
            'What are transformers in AI?',
            'Define reinforcement learning'
        ]

    prompt_index = 0

    print('\n🚀 Starting live monitoring...')
    print(f'📊 Refresh interval: {interval}s')
    print(f'📝 Test prompts: {len(test_prompts)}')
    print('\nInitializing...\n')

    await asyncio.sleep(2)

    try:
        while True:
            # Select prompt
            if rotate_prompts:
                prompt = test_prompts[prompt_index % len(test_prompts)]
                prompt_index += 1
            else:
                prompt = test_prompts[0]

            try:
                provider, text, duration, metadata = await call_vercel(prompt)
                monitor.record(provider, duration)
            except Exception as e:
                monitor.record_error(str(e))

            monitor.display_stats()
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print('\n\n✅ Monitoring stopped')

        # Final summary
        stats = monitor.get_stats()
        print('\n' + '╔' + '═' * 68 + '╗')
        print('║' + ' ' * 20 + '📊 FINAL SUMMARY' + ' ' * 31 + '║')
        print('╚' + '═' * 68 + '╝\n')
        print(f'  Total Runtime: {stats["uptime"]:.0f}s')
        print(f'  Total Requests: {monitor.total_requests}')
        print(f'  Success Rate: {stats["success_rate"]:.1f}%')
        print(f'  Average Latency: {stats["avg_latency"]:.3f}s')
        print(f'  Average Throughput: {stats["requests_per_second"]:.2f} req/s')

        if stats.get('provider_distribution'):
            print(f'\n  Provider Usage:')
            for provider, count in sorted(stats['provider_distribution'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(monitor.providers)) * 100
                print(f'    {provider:12s} {count:3d} requests ({percentage:5.1f}%)')

        print('\n' + '═' * 70 + '\n')


if __name__ == '__main__':
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    # Custom prompts from command line
    custom_prompts = sys.argv[2:] if len(sys.argv) > 2 else None

    try:
        asyncio.run(monitor_loop(interval, custom_prompts))
    except KeyboardInterrupt:
        sys.exit(0)
