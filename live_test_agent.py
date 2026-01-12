#!/usr/bin/env python3
"""
Live Test Agent - Enhanced Production Version
fix/python-tests-and-mcp-configuration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Calls live Vercel endpoint
✅ Streams AI responses
✅ Pushes metrics to Grafana Cloud
✅ Validates provider fallback
✅ Error handling & retry logic
 main
"""
import asyncio
import aiohttp
import time
import os
import sys
from prometheus_client import Histogram, Counter, CollectorRegistry
from typing import Tuple, Optional
import json

 fix/python-tests-and-mcp-configuration
# Configuration

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main
VERCEL_URL = os.getenv(
    'VERCEL_URL',
    'https://the-lab-verse-monitoring.vercel.app/api/research'
)
 fix/python-tests-and-mcp-configuration


 main
GRAFANA_PUSH_URL = os.getenv('GRAFANA_CLOUD_PROM_URL', '')
GRAFANA_USER = os.getenv('GRAFANA_CLOUD_PROM_USER', '')
GRAFANA_PASS = os.getenv('GRAFANA_CLOUD_API_KEY', '')

 fix/python-tests-and-mcp-configuration
# Prometheus Metrics
registry = CollectorRegistry()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Prometheus Metrics (matches backend exactly)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
registry = CollectorRegistry()

main
latency_histogram = Histogram(
    'ai_provider_request_duration_seconds',
    'Request latency from Python agent',
    labelnames=['provider', 'model', 'source'],
    registry=registry,
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

request_counter = Counter(
    'ai_provider_request_total',
    'Total requests from Python agent',
    labelnames=['provider', 'model', 'status', 'source'],
    registry=registry
)

error_counter = Counter(
    'ai_provider_errors_total',
    'Total errors from Python agent',
    labelnames=['provider', 'error_type', 'source'],
    registry=registry
)

 fix/python-tests-and-mcp-configuration


 main
async def push_to_grafana():
    """Push metrics to Grafana Cloud via remote write."""
    if not all([GRAFANA_PUSH_URL, GRAFANA_USER, GRAFANA_PASS]):
        return False
 fix/python-tests-and-mcp-configuration
    
    try:
        from prometheus_client import exposition
        metrics_data = exposition.generate_latest(registry)



    try:
        from prometheus_client import exposition
        metrics_data = exposition.generate_latest(registry)

 main
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GRAFANA_PUSH_URL,
                data=metrics_data,
                headers={'Content-Type': 'text/plain'},
                auth=aiohttp.BasicAuth(GRAFANA_USER, GRAFANA_PASS),
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    return True
                else:
                    print(f'⚠️  Grafana push failed: HTTP {resp.status}')
                    return False
    except Exception as e:
        print(f'⚠️  Grafana push error: {e}')
        return False

 fix/python-tests-and-mcp-configuration


 main
async def call_vercel(
    prompt: str,
    timeout: int = 30,
    max_retries: int = 3
) -> Tuple[str, str, float, dict]:
 fix/python-tests-and-mcp-configuration
    """Call Vercel endpoint with retry logic."""
    body = {'q': prompt}

    for attempt in range(max_retries):
        t0 = time.time()

    """
    Call Vercel endpoint with retry logic.

    Args:
        prompt: Question to ask
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts

    Returns:
        Tuple of (provider, text, duration, metadata)
    """
    body = {'q': prompt}

    for attempt in range(max_retries):
        t0 = time.time()

 main
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    VERCEL_URL,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    duration = time.time() - t0
 fix/python-tests-and-mcp-configuration

                    if resp.status != 200:
                        error_text = await resp.text()
                        raise aiohttp.ClientError(f'HTTP {resp.status}: {error_text}')

                    data = await resp.json()
                    provider = data.get('provider', 'unknown')
                    text = data.get('text', '')
                    model = data.get('model', 'default')



                    if resp.status != 200:
                        error_text = await resp.text()
                        raise aiohttp.ClientError(f'HTTP {resp.status}: {error_text}')

                    data = await resp.json()

                    provider = data.get('provider', 'unknown')
                    text = data.get('text', '')
                    model = data.get('model', 'default')

 main
                    # Record success metrics
                    latency_histogram.labels(
                        provider=provider,
                        model=model,
                        source='python-agent'
                    ).observe(duration)
 fix/python-tests-and-mcp-configuration



 main
                    request_counter.labels(
                        provider=provider,
                        model=model,
                        status='success',
                        source='python-agent'
                    ).inc()
 fix/python-tests-and-mcp-configuration

                    # Push to Grafana
                    await push_to_grafana()



                    # Push to Grafana
                    await push_to_grafana()

 main
                    metadata = {
                        'attempt': attempt + 1,
                        'model': model,
                        'response_length': len(text),
                        'timestamp': time.time()
                    }
 fix/python-tests-and-mcp-configuration

                    return provider, text, duration, metadata



                    return provider, text, duration, metadata

 main
        except asyncio.TimeoutError:
            duration = time.time() - t0
            error_counter.labels(
                provider='unknown',
                error_type='timeout',
                source='python-agent'
            ).inc()
 fix/python-tests-and-mcp-configuration



 main
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f'⏱️  Timeout on attempt {attempt + 1}, retrying in {wait_time}s...')
                await asyncio.sleep(wait_time)
            else:
                raise Exception(f'Request timed out after {max_retries} attempts')
 fix/python-tests-and-mcp-configuration



 main
        except aiohttp.ClientError as e:
            error_counter.labels(
                provider='unknown',
                error_type='client_error',
                source='python-agent'
            ).inc()
 fix/python-tests-and-mcp-configuration



 main
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f'❌ Error on attempt {attempt + 1}: {e}')
                print(f'   Retrying in {wait_time}s...')
                await asyncio.sleep(wait_time)
            else:
                raise
 fix/python-tests-and-mcp-configuration



 main
        except Exception as e:
            error_counter.labels(
                provider='unknown',
                error_type='unknown',
                source='python-agent'
            ).inc()
            raise

 fix/python-tests-and-mcp-configuration
def print_result(provider: str, text: str, duration: float, metadata: dict):
    """Pretty-print the result with enhanced formatting."""
    print('\n' + '═' * 70)
    print(f'🤖 Provider: {provider}')
    print(f'📦 Model: {metadata.get("model", "N/A")}')
    print(f'⏱️  Latency: {duration:.3f}s')
    print(f'📝 Response Length: {metadata.get("response_length", 0)} chars')
    print(f'🔄 Attempt: {metadata.get("attempt", 1)}')
    print('═' * 70)
    print(f'💬 Response:')
    print(f'{text[:500]}{"..." if len(text) > 500 else ""}')
    print('═' * 70 + '\n')

def print_banner():
    """Print startup banner."""
    print('\n' + '╔' * 70)
    print('🚀 LIVE TEST AGENT - Production Version')
    print('╔' * 70)
    print(f'🔗 Endpoint: {VERCEL_URL}')
    print(f'📊 Grafana: {"✅ Configured" if GRAFANA_PUSH_URL else "⚠️  Not configured"}')
    print('╔' * 70 + '\n')


def print_result(provider: str, text: str, duration: float, metadata: dict):
    """Pretty-print the result with enhanced formatting."""
    print('\n' + '━' * 70)
    print(f'🤖 Provider: {provider}')
    print(f'📦 Model: {metadata.get("model", "N/A")}')
    print(f'⏱️  Latency: {duration:.3f}s')
    print(f'📏 Response Length: {metadata.get("response_length", 0)} chars')
    print(f'🔄 Attempt: {metadata.get("attempt", 1)}')
    print('━' * 70)
    print(f'💬 Response:')
    print(f'{text[:500]}{"..." if len(text) > 500 else ""}')
    print('━' * 70 + '\n')


def print_banner():
    """Print startup banner."""
    print('\n' + '═' * 70)
    print('🚀 LIVE TEST AGENT - Production Version')
    print('═' * 70)
    print(f'📍 Endpoint: {VERCEL_URL}')
    print(f'📊 Grafana: {"✅ Configured" if GRAFANA_PUSH_URL else "⚠️  Not configured"}')
    print('═' * 70 + '\n')

 main

async def health_check() -> bool:
    """Verify endpoint is reachable."""
    health_url = VERCEL_URL.replace('/api/research', '/health')
 fix/python-tests-and-mcp-configuration



 main
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    print('✅ Health check passed')
                    return True
                else:
                    print(f'⚠️  Health check returned HTTP {resp.status}')
                    return False
    except Exception as e:
        print(f'❌ Health check failed: {e}')
        return False

 fix/python-tests-and-mcp-configuration
async def main():
    """Main execution flow."""
    print_banner()



async def main():
    """Main execution flow."""
    print_banner()

 main
    # Health check
    print('🔍 Running health check...')
    if not await health_check():
        print('⚠️  Warning: Health check failed, but continuing anyway...\n')
    else:
        print()
 fix/python-tests-and-mcp-configuration



 main
    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
    else:
        prompt = 'What did Anthropic announce today?'
 fix/python-tests-and-mcp-configuration

    print(f'📝 Prompt: {prompt}')
    print(f'🔄 Calling endpoint...\n')

    try:
        # Execute request
        provider, text, duration, metadata = await call_vercel(prompt)

        # Display results
        print_result(provider, text, duration, metadata)

        # Success indicators
        print('✅ Request completed successfully')


    print(f'📝 Prompt: {prompt}')
    print(f'🔄 Calling endpoint...\n')

    try:
        # Execute request
        provider, text, duration, metadata = await call_vercel(prompt)

        # Display results
        print_result(provider, text, duration, metadata)

        # Success indicators
        print('✅ Request completed successfully')

 main
        if GRAFANA_PUSH_URL:
            print('📊 Metrics pushed to Grafana Cloud')
            print('⏳ Check dashboard in 10-30 seconds for updated metrics')
        else:
            print('⚠️  Grafana not configured - metrics not pushed')
 fix/python-tests-and-mcp-configuration

        print(f'\n🎯 Provider used: {provider}')
        print(f'⚡ Performance: {duration:.3f}s latency')



        print(f'\n🎯 Provider used: {provider}')
        print(f'⚡ Performance: {duration:.3f}s latency')

 main
        # Performance rating
        if duration < 1.0:
            print('🏆 Excellent performance!')
        elif duration < 3.0:
            print('✅ Good performance')
        elif duration < 5.0:
            print('⚠️  Acceptable performance')
        else:
            print('🐌 Slow performance - check provider status')
 fix/python-tests-and-mcp-configuration

        return 0



        return 0

 main
    except Exception as e:
        print(f'\n❌ Request failed: {e}')
        print(f'🔧 Troubleshooting:')
        print(f'   1. Verify endpoint is accessible: {VERCEL_URL}')
        print(f'   2. Check your internet connection')
        print(f'   3. Verify API keys are configured in Vercel')
        print(f'   4. Check Vercel deployment logs')
        return 1

 fix/python-tests-and-mcp-configuration


 main
if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(0)
