#!/usr/bin/env python3
"""
Grafana Metrics Validator - Enhanced Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies metrics are flowing correctly to Grafana Cloud
Validates data integrity and alert configurations
"""
from datetime import datetime
import os
import sys

import requests


class GrafanaValidator:
    """Validates Grafana Cloud metrics and configuration."""

    def __init__(self):
        self.base_url = os.getenv('GRAFANA_CLOUD_PROM_URL', '').replace('/api/prom/push', '')
        self.user = os.getenv('GRAFANA_CLOUD_PROM_USER', '')
        self.api_key = os.getenv('GRAFANA_CLOUD_API_KEY', '')

        if not all([self.base_url, self.user, self.api_key]):
            print('⚠️  Grafana credentials not configured. Skipping validation.')
            sys.exit(0)

    def query(self, query: str, time_param: str | None = None) -> dict | None:
        """Execute PromQL query against Grafana Cloud."""
        query_url = f'{self.base_url}/api/prom/api/v1/query'

        params = {
            'query': query,
            'time': time_param or datetime.now().isoformat()
        }

        try:
            response = requests.get(
                query_url,
                params=params,
                auth=(self.user, self.api_key),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'❌ Query failed: {e}')
            return None

    def query_range(self, query: str, start: str, end: str, step: str = '15s') -> dict | None:
        """Execute range query against Grafana Cloud."""
        query_url = f'{self.base_url}/api/prom/api/v1/query_range'

        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }

        try:
            response = requests.get(
                query_url,
                params=params,
                auth=(self.user, self.api_key),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'❌ Range query failed: {e}')
            return None


def validate_metrics():
    """Validate all expected metrics exist and are reporting."""
    validator = GrafanaValidator()

    print('╔' + '═' * 68 + '╗')
    print('║' + ' ' * 15 + '🔍 GRAFANA METRICS VALIDATION' + ' ' * 22 + '║')
    print('╚' + '═' * 68 + '╝\n')

    metrics_to_check = [
        {
            'name': 'Request Total',
            'query': 'ai_provider_request_total',
            'description': 'Total number of requests per provider',
            'expected_labels': ['provider', 'model', 'status']
        },
        {
            'name': 'Error Total',
            'query': 'ai_provider_errors_total',
            'description': 'Total number of errors per provider',
            'expected_labels': ['provider', 'error_type']
        },
        {
            'name': 'Request Duration',
            'query': 'ai_provider_request_duration_seconds',
            'description': 'Request latency histogram',
            'expected_labels': ['provider', 'model']
        },
        {
            'name': 'Token Usage',
            'query': 'ai_provider_tokens_total',
            'description': 'Total tokens consumed',
            'expected_labels': ['provider', 'model']
        },
        {
            'name': 'Python Agent Metrics',
            'query': 'ai_provider_request_duration_seconds{source="python-agent"}',
            'description': 'Metrics from Python test agent',
            'expected_labels': ['provider', 'model', 'source']
        }
    ]

    results = []

    for metric in metrics_to_check:
        print(f'\n{"─" * 70}')
        print(f'📊 Checking: {metric["name"]}')
        print(f'   {metric["description"]}')
        print(f'   Query: {metric["query"]}')

        result = validator.query(metric['query'])

        if result and result.get('status') == 'success':
            data = result.get('data', {})
            result_data = data.get('result', [])

            if result_data:
                print(f'   ✅ Metric found: {len(result_data)} series')

                # Check labels
                sample = result_data[0].get('metric', {})
                found_labels = set(sample.keys())
                expected_labels = set(metric.get('expected_labels', []))

                if expected_labels.issubset(found_labels):
                    print(f'   ✅ Labels validated: {", ".join(expected_labels)}')
                else:
                    missing = expected_labels - found_labels
                    print(f'   ⚠️  Missing labels: {", ".join(missing)}')

                # Show sample values
                print('   📈 Sample series:')
                for i, series in enumerate(result_data[:3]):  # Show first 3
                    metric_labels = series.get('metric', {})
                    value = series.get('value', [None, 'N/A'])[1]
                    labels_str = ', '.join([f'{k}={v}' for k, v in metric_labels.items()])
                    print(f'      {i+1}. {labels_str} = {value}')

                results.append({
                    'name': metric['name'],
                    'status': 'success',
                    'series_count': len(result_data)
                })
            else:
                print('   ⚠️  Metric exists but no data')
                results.append({
                    'name': metric['name'],
                    'status': 'no_data'
                })
        else:
            print('   ❌ Metric not found or query failed')
            results.append({
                'name': metric['name'],
                'status': 'failed'
            })

    # Summary
    print(f'\n{"═" * 70}')
    print('📊 VALIDATION SUMMARY')
    print(f'{"═" * 70}\n')

    successful = [r for r in results if r['status'] == 'success']
    no_data = [r for r in results if r['status'] == 'no_data']
    failed = [r for r in results if r['status'] == 'failed']

    print(f'✅ Metrics with data: {len(successful)}/{len(results)}')
    print(f'⚠️  Metrics without data: {len(no_data)}/{len(results)}')
    print(f'❌ Failed metrics: {len(failed)}/{len(results)}')

    if no_data:
        print('\n⚠️  Metrics without data:')
        for r in no_data:
            print(f'   - {r["name"]}')
        print('\n💡 Tip: Run live_test_agent.py to generate data')

    if failed:
        print('\n❌ Failed metrics:')
        for r in failed:
            print(f'   - {r["name"]}')

    print(f'\n{"═" * 70}\n')

    return len(failed) == 0 and len(no_data) == 0


def check_data_freshness():
    """Check if metrics are being updated recently."""
    validator = GrafanaValidator()

    print('╔' + '═' * 68 + '╗')
    print('║' + ' ' * 18 + '🕐 DATA FRESHNESS CHECK' + ' ' * 26 + '║')
    print('╚' + '═' * 68 + '╝\n')

    # Check last update time
    query = 'ai_provider_request_total'
    result = validator.query(query)

    if result and result.get('status') == 'success':
        data = result.get('data', {})
        result_data = data.get('result', [])

        if result_data:
            latest_timestamp = 0
            for series in result_data:
                timestamp = float(series.get('value', [0, 0])[0])
                latest_timestamp = max(latest_timestamp, timestamp)

            if latest_timestamp > 0:
                last_update = datetime.fromtimestamp(latest_timestamp)
                age_seconds = (datetime.now() - last_update).total_seconds()

                print(f'📅 Last Update: {last_update.strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'⏱️  Age: {age_seconds:.0f} seconds ago')

                if age_seconds < 60:
                    print('✅ Data is fresh (< 1 minute old)')
                    return True
                elif age_seconds < 300:
                    print(f'⚠️  Data is slightly stale ({age_seconds/60:.1f} minutes old)')
                    return True
                else:
                    print(f'❌ Data is stale ({age_seconds/60:.1f} minutes old)')
                    print('💡 Check if metrics push is working')
                    return False
            else:
                print('❌ No timestamp data available')
                return False
        else:
            print('❌ No data found')
            return False
    else:
        print('❌ Query failed')
        return False


def validate_slo_query():
    """Validate the SLO availability query works correctly."""
    validator = GrafanaValidator()

    print('\n╔' + '═' * 68 + '╗')
    print('║' + ' ' * 20 + '🎯 SLO QUERY VALIDATION' + ' ' * 23 + '║')
    print('╚' + '═' * 68 + '╝\n')

    slo_query = (
        '1 - (sum(rate(ai_provider_errors_total[5m])) / '
        'sum(rate(ai_provider_request_total[5m])))'
    )

    print(f'Query: {slo_query}\n')

    result = validator.query(slo_query)

    if result and result.get('status') == 'success':
        data = result.get('data', {})
        result_data = data.get('result', [])

        if result_data and len(result_data) > 0:
            value = float(result_data[0].get('value', [None, 0])[1])
            percentage = value * 100

            print('✅ SLO Query successful')
            print(f'📊 Current Availability: {percentage:.2f}%')

            if percentage >= 99:
                print('🏆 Excellent availability (≥ 99%)')
            elif percentage >= 95:
                print('✅ Good availability (≥ 95%)')
            elif percentage >= 90:
                print('⚠️  Acceptable availability (≥ 90%)')
            else:
                print('❌ Poor availability (< 90%)')

            return True
        else:
            print('⚠️  Query returned no data')
            print('💡 This is normal if no requests have been made recently')
            return False
    else:
        print('❌ SLO query failed')
        return False


def check_provider_distribution():
    """Check distribution of requests across providers."""
    validator = GrafanaValidator()

    print('\n╔' + '═' * 68 + '╗')
    print('║' + ' ' * 16 + '🔄 PROVIDER DISTRIBUTION' + ' ' * 26 + '║')
    print('╚' + '═' * 68 + '╝\n')

    query = 'sum(ai_provider_request_total) by (provider)'
    result = validator.query(query)

    if result and result.get('status') == 'success':
        data = result.get('data', {})
        result_data = data.get('result', [])

        if result_data:
            providers = []
            total_requests = 0

            for series in result_data:
                provider = series.get('metric', {}).get('provider', 'unknown')
                count = float(series.get('value', [None, 0])[1])
                providers.append({'provider': provider, 'count': count})
                total_requests += count

            providers.sort(key=lambda x: x['count'], reverse=True)

            print(f'Total Requests: {int(total_requests)}\n')
            print(f'{"Provider":<15} {"Requests":<12} {"Percentage":<12} {"Bar"}')
            print('─' * 70)

            for p in providers:
                percentage = (p['count'] / total_requests * 100) if total_requests > 0 else 0
                bar = '█' * int(percentage / 2)
                print(f'{p["provider"]:<15} {int(p["count"]):<12} {percentage:>6.1f}%     {bar}')

            # Check if fallback is working
            if len(providers) > 1:
                print('\n✅ Multiple providers active - fallback working')
            else:
                print('\n⚠️  Only one provider active - verify fallback configuration')

            return True
        else:
            print('⚠️  No provider data found')
            return False
    else:
        print('❌ Query failed')
        return False


def check_latency_percentiles():
    """Check latency percentiles across providers."""
    validator = GrafanaValidator()

    print('\n╔' + '═' * 68 + '╗')
    print('║' + ' ' * 18 + '⚡ LATENCY PERCENTILES' + ' ' * 27 + '║')
    print('╚' + '═' * 68 + '╝\n')

    percentiles = [50, 95, 99]

    for p in percentiles:
        query = (
            f'histogram_quantile({p/100}, '
            'sum(rate(ai_provider_request_duration_seconds_bucket[5m])) by (le, provider))'
        )
        result = validator.query(query)

        if result and result.get('status') == 'success':
            data = result.get('data', {})
            result_data = data.get('result', [])

            if result_data:
                print(f'P{p} Latency:')
                for series in result_data:
                    provider = series.get('metric', {}).get('provider', 'unknown')
                    latency = float(series.get('value', [None, 0])[1])
                    print(f'  {provider:<12} {latency:.3f}s')
                print()


def run_comprehensive_validation():
    """Run all validation checks."""
    print('\n' + '╔' + '═' * 68 + '╗')
    print('║' + ' ' * 10 + '🔍 COMPREHENSIVE GRAFANA VALIDATION' + ' ' * 21 + '║')
    print('╚' + '═' * 68 + '╝\n')

    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    results = {
        'metrics': validate_metrics(),
        'freshness': check_data_freshness(),
        'slo': validate_slo_query(),
        'providers': check_provider_distribution()
    }

    check_latency_percentiles()

    # Final summary
    print('╔' + '═' * 68 + '╗')
    print('║' + ' ' * 22 + '📊 FINAL RESULTS' + ' ' * 29 + '║')
    print('╚' + '═' * 68 + '╝\n')

    all_passed = all(results.values())

    print(f'Metrics Validation:      {"✅ PASSED" if results["metrics"] else "❌ FAILED"}')
    print(f'Data Freshness:          {"✅ PASSED" if results["freshness"] else "❌ FAILED"}')
    print(f'SLO Query:               {"✅ PASSED" if results["slo"] else "⚠️  NO DATA"}')
    print(f'Provider Distribution:   {"✅ PASSED" if results["providers"] else "⚠️  NO DATA"}')

    print('\n' + '─' * 70)

    if all_passed:
        print('🎉 All validations passed!')
        print('✅ Grafana Cloud is properly configured and receiving metrics')
    else:
        print('⚠️  Some validations failed or returned no data')
        print('\n💡 Troubleshooting steps:')
        if not results['metrics']:
            print('   1. Verify GRAFANA_CLOUD_* environment variables are set')
            print('   2. Check Grafana Cloud credentials are valid')
        if not results['freshness']:
            print('   3. Verify pushToGrafana.js is running')
            print('   4. Check Vercel deployment logs for errors')
        if not results['slo'] or not results['providers']:
            print('   5. Run live_test_agent.py to generate test data')
            print('   6. Wait 30-60 seconds for metrics to propagate')

    print('\n' + '═' * 70 + '\n')

    return all_passed


if __name__ == '__main__':
    try:
        success = run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print('\n\n⚠️  Validation interrupted by user')
        sys.exit(130)
    except Exception as e:
        print(f'\n❌ Unexpected error: {e}')
        sys.exit(1)
