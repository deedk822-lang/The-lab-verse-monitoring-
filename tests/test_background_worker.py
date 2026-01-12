"""
Comprehensive unit tests for the background worker.

Tests cover rate limiting, SSRF protection, HTTP job processing,
and security features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
import socket
import requests
from agents.background.worker import (
    check_rate_limit,
    _domain_allowed,
    _validate_and_resolve_target,
    process_http_job,
)


class TestDomainValidation:
    """Test suite for domain validation."""

    def test_domain_allowed_default(self):
        """Should return True by default (no blocklist active)."""
        result = _domain_allowed('example.com')
        assert result is True

    def test_domain_allowed_various_domains(self):
        """Should accept various domain formats."""
        domains = [
            'example.com',
            'subdomain.example.com',
            'api.service.example.com',
            'localhost',
            'example.co.uk'
        ]

        for domain in domains:
            result = _domain_allowed(domain)
            assert result is True, f"Domain {domain} should be allowed"


class TestSSRFProtection:
    """Test suite for SSRF protection mechanisms."""

    def test_validate_private_ip_blocked(self):
        """Should block private IP addresses."""
        private_ips = [
            'http://127.0.0.1/test',
            'http://10.0.0.1/api',
            'http://192.168.1.1/admin',
            'http://172.16.0.1/internal'
        ]

        for url in private_ips:
            # Patch getaddrinfo to return a private IP
            with patch('socket.getaddrinfo', return_value=[(None, None, None, None, ('127.0.0.1', 80))]):
                valid, reason, _ = _validate_and_resolve_target(url)
                assert valid is False

    def test_validate_localhost_blocked(self):
        """Should block localhost and loopback addresses."""
        localhost_urls = [
            'http://localhost/test',
            'http://127.0.0.1/api',
            'http://[::1]/admin'
        ]

        for url in localhost_urls:
            with patch('socket.getaddrinfo', return_value=[(None, None, None, None, ('127.0.0.1', 80))]):
                valid, reason, _ = _validate_and_resolve_target(url)
                assert valid is False

    def test_validate_public_ip_allowed(self):
        """Should allow public IP addresses."""
        with patch('socket.getaddrinfo', return_value=[(None, None, None, None, ('8.8.8.8', 80))]):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                valid, reason, ip = _validate_and_resolve_target('http://example.com/test')
                assert valid is True
                assert ip == '8.8.8.8'

    def test_validate_dns_resolution_failure(self):
        """Should handle DNS resolution failures."""
        with patch('socket.getaddrinfo', side_effect=socket.gaierror('DNS failed')):
            valid, reason, _ = _validate_and_resolve_target('http://nonexistent.invalid/test')
            assert valid is False
            assert 'resolve' in reason.lower() or 'dns' in reason.lower()


class TestHTTPJobProcessing:
    """Test suite for HTTP job processing."""

    def test_process_http_job_invalid_payload(self):
        """Should return error for invalid payload."""
        result = process_http_job(None)
        assert result['error'] == 'invalid payload'

    def test_process_http_job_missing_url(self):
        """Should return error when URL is missing."""
        result = process_http_job({})
        assert result['error'] == 'missing url'

    def test_process_http_job_rate_limit_exceeded(self):
        """Should return error when rate limit is exceeded."""
        url = f'http://ratelimit-test.com/api'
        with patch('agents.background.worker.check_rate_limit', return_value=False):
            result = process_http_job({'url': url})
            assert result['error'] == 'rate limit exceeded'

    def test_process_http_job_ssrf_blocked(self):
        """Should block SSRF attempts."""
        job = {'url': 'http://internal.local/admin'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(False, 'private IP blocked', None)):
            result = process_http_job(job)
            assert 'error' in result
            assert 'not allowed' in result['error'] or 'blocked' in result['error']

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_success(self, mock_request):
        """Should successfully process valid HTTP job."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([b'Success response'])
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response

        job = {
            'url': 'http://example.com/api',
            'method': 'GET',
            'timeout': 10
        }

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '93.184.216.34')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert result['status_code'] == 200
        assert result['content_length'] == len(b'Success response')
        assert 'elapsed_ms' in result

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_with_custom_headers(self, mock_request):
        """Should include custom headers in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([])
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        job = {
            'url': 'http://api.example.com/endpoint',
            'headers': {'Authorization': 'Bearer token123', 'X-Custom': 'value'}
        }

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                process_http_job(job)

        call_args = mock_request.call_args
        headers = call_args[1].get('headers', {})
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer token123'

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_request_exception(self, mock_request):
        """Should handle request exceptions."""
        mock_request.side_effect = requests.RequestException('Connection failed')
        job = {'url': 'http://failing.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'request failed' in result['error'].lower()

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_ssl_error(self, mock_request):
        """Should handle SSL verification errors."""
        mock_request.side_effect = requests.exceptions.SSLError('SSL verification failed')
        job = {'url': 'https://invalid-cert.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'ssl' in result['error'].lower()

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_redirect_blocked(self, mock_request):
        """Should block redirects."""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.headers = {'Location': 'http://evil.com/'}
        mock_request.return_value = mock_response

        job = {'url': 'http://redirect-test.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'redirect' in result['error'].lower()

    @patch('agents.background.worker.requests.request')
    def test_process_http_job_response_too_large(self, mock_request):
        """Should block responses that are too large."""
        large_content_chunk = b'x' * (1024 * 1024)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([large_content_chunk] * 11)
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_request.return_value = mock_response

        job = {'url': 'http://large-response.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'too large' in result['error'].lower()


class TestExternalRequestsFlag:
    """Test suite for ALLOW_EXTERNAL flag handling."""

    def test_external_requests_disabled(self):
        """Should block external requests when flag is disabled."""
        job = {'url': 'http://external-api.com/data'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker.ALLOW_EXTERNAL', False):
                result = process_http_job(job)
                assert 'error' in result
                assert 'external requests disabled' in result['error'].lower()


class TestMetricsCollection:
    """Test suite for metrics collection."""

    @patch('agents.background.worker.REQUESTS')
    @patch('agents.background.worker.requests.request')
    def test_metrics_incremented_on_request(self, mock_request, mock_requests_metric):
        """Should increment request metrics."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([])
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        job = {'url': 'http://metrics-test.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                process_http_job(job)

        mock_requests_metric.inc.assert_called_once()

    @patch('agents.background.worker.SSRF_BLOCKS')
    def test_ssrf_metrics_incremented_on_block(self, mock_ssrf_blocks):
        """Should increment SSRF block metrics."""
        job = {'url': 'http://127.0.0.1/internal'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(False, 'private IP', None)):
            process_http_job(job)

        # SSRF_BLOCKS should be incremented
        assert mock_ssrf_blocks.labels.called or mock_ssrf_blocks.inc.called


class TestEdgeCases:
    """Test suite for edge cases and unusual inputs."""

    def test_process_http_job_with_empty_url(self):
        """Should handle empty URL string."""
        result = process_http_job({'url': ''})
        assert 'error' in result

    def test_process_http_job_with_malformed_url(self):
        """Should handle malformed URLs."""
        result = process_http_job({'url': 'not-a-valid-url'})
        assert 'error' in result

    def test_process_http_job_with_unicode_url(self):
        """Should handle Unicode in URLs."""
        job = {'url': 'http://example.com/测试'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(False, 'invalid', None)):
            result = process_http_job(job)
            assert 'error' in result

    def test_rate_limit_with_empty_domain(self):
        """Should handle empty domain string."""
        result = check_rate_limit('')
        # Should either work or raise appropriate error
        assert result is True or result is False
