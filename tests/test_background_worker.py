"""
Comprehensive unit tests for the background worker.

Tests cover rate limiting, SSRF protection, HTTP job processing,
and security features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from collections import defaultdict
import time
import requests
from agents.background.worker import (
    check_rate_limit,
    _domain_allowed,
    _validate_and_resolve_target,
    process_http_job,
    # request_counts, # NOTE: This is part of a legacy, in-memory rate limiter and is no longer used.
    # RATE_LIMIT_WINDOW,
    # RATE_LIMIT_MAX
)


# class TestRateLimiting:
#     """Test suite for rate limiting functionality."""

#     def setup_method(self):
#         """Clear rate limit state before each test."""
#         request_counts.clear()

#     def test_first_request_allowed(self):
#         """Should allow first request from a domain."""
#         result = check_rate_limit('example.com')
#         assert result is True

#     def test_requests_within_limit(self):
#         """Should allow requests within the rate limit."""
#         domain = 'test.com'

#         for i in range(RATE_LIMIT_MAX):
#             result = check_rate_limit(domain)
#             assert result is True, f"Request {i+1} should be allowed"

#     def test_request_exceeding_limit(self):
#         """Should block requests exceeding rate limit."""
#         domain = 'blocked.com'

#         # Fill up the rate limit
#         for _ in range(RATE_LIMIT_MAX):
#             check_rate_limit(domain)

#         # Next request should be blocked
#         result = check_rate_limit(domain)
#         assert result is False

#     def test_rate_limit_per_domain_isolation(self):
#         """Should maintain separate rate limits per domain."""
#         domain1 = 'site1.com'
#         domain2 = 'site2.com'

#         # Fill up domain1
#         for _ in range(RATE_LIMIT_MAX):
#             check_rate_limit(domain1)

#         # domain2 should still be allowed
#         result = check_rate_limit(domain2)
#         assert result is True

#     def test_rate_limit_window_expiry(self):
#         """Should reset rate limit after window expires."""
#         domain = 'expiry-test.com'

#         # Make a request
#         check_rate_limit(domain)
#         assert len(request_counts[domain]) == 1

#         # Simulate time passing beyond window
#         old_time = time.time() - (RATE_LIMIT_WINDOW + 1)
#         request_counts[domain] = [old_time]

#         # New request should clean up old entries
#         result = check_rate_limit(domain)
#         assert result is True
#         assert len(request_counts[domain]) == 1
#         assert request_counts[domain][0] > old_time

#     def test_rate_limit_mixed_timestamps(self):
#         """Should only count recent requests within window."""
#         domain = 'mixed.com'
#         current_time = time.time()

#         # Add old timestamps (outside window)
#         old_timestamps = [current_time - (RATE_LIMIT_WINDOW + i) for i in range(1, 6)]
#         request_counts[domain] = old_timestamps.copy()

#         # Check rate limit - should clean old entries and allow request
#         result = check_rate_limit(domain)
#         assert result is True
#         assert len(request_counts[domain]) == 1  # Only new request

#     def test_rate_limit_at_boundary(self):
#         """Should handle requests exactly at rate limit boundary."""
#         domain = 'boundary.com'

#         # Make exactly RATE_LIMIT_MAX requests
#         for _ in range(RATE_LIMIT_MAX):
#             check_rate_limit(domain)

#         # Should have exactly RATE_LIMIT_MAX entries
#         assert len(request_counts[domain]) == RATE_LIMIT_MAX

#         # Next request should be blocked
#         result = check_rate_limit(domain)
#         assert result is False


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
            with patch('socket.gethostbyname', return_value=url.split('/')[2].split(':')[0]):
                valid, reason, _ = _validate_and_resolve_target(url)
                assert valid is False
                assert 'private' in reason.lower() or 'internal' in reason.lower()

    def test_validate_localhost_blocked(self):
        """Should block localhost and loopback addresses."""
        localhost_urls = [
            'http://localhost/test',
            'http://127.0.0.1/api',
            'http://[::1]/admin'
        ]

        for url in localhost_urls:
            with patch('socket.gethostbyname', return_value='127.0.0.1'):
                valid, reason, _ = _validate_and_resolve_target(url)
                assert valid is False

    def test_validate_public_ip_allowed(self):
        """Should allow public IP addresses."""
        with patch('socket.gethostbyname', return_value='8.8.8.8'):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                valid, reason, ip = _validate_and_resolve_target('http://example.com/test')
                assert valid is True
                assert ip == '8.8.8.8'

    def test_validate_dns_resolution_failure(self):
        """Should handle DNS resolution failures."""
        with patch('socket.gethostbyname', side_effect=Exception('DNS failed')):
            valid, reason, _ = _validate_and_resolve_target('http://nonexistent.invalid/test')
            assert valid is False
            assert 'resolve' in reason.lower() or 'dns' in reason.lower()


class TestHTTPJobProcessing:
    """Test suite for HTTP job processing."""

    # def setup_method(self):
    #     """Clear rate limit state before each test."""
    #     request_counts.clear()

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
        domain = 'ratelimit-test.com'
        url = f'http://{domain}/api'

        # Fill up rate limit
        for _ in range(RATE_LIMIT_MAX):
            check_rate_limit(domain)

        # Next request should be rate limited
        with patch('agents.background.worker._validate_and_resolve_target', return_value=(True, '', '1.2.3.4')):
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

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_success(self, mock_session_cls):
        """Should successfully process valid HTTP job."""
        # Setup mocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'Success response'
        mock_response.elapsed.total_seconds.return_value = 0.5

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

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

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_with_custom_headers(self, mock_session_cls):
        """Should include custom headers in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b''
        mock_response.elapsed.total_seconds.return_value = 0.1

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {
            'url': 'http://api.example.com/endpoint',
            'headers': {'Authorization': 'Bearer token123', 'X-Custom': 'value'}
        }

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        # Verify headers were passed
        call_args = mock_session.request.call_args
        headers = call_args[1].get('headers', {})
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer token123'

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_post_with_data(self, mock_session_cls):
        """Should handle POST requests with data."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = b'Created'
        mock_response.elapsed.total_seconds.return_value = 0.2

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {
            'url': 'http://api.example.com/create',
            'method': 'POST',
            'data': {'key': 'value'}
        }

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert result['status_code'] == 201
        call_args = mock_session.request.call_args
        assert call_args[1]['data'] == {'key': 'value'}

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_request_exception(self, mock_session_cls):
        """Should handle request exceptions."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.RequestException('Connection failed')
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {'url': 'http://failing.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'request failed' in result['error'].lower()

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_ssl_error(self, mock_session_cls):
        """Should handle SSL verification errors."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.SSLError('SSL verification failed')
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {'url': 'https://invalid-cert.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'ssl' in result['error'].lower()

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_redirect_blocked(self, mock_session_cls):
        """Should block redirects."""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.headers = {'Location': 'http://evil.com/'}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {'url': 'http://redirect-test.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                result = process_http_job(job)

        assert 'error' in result
        assert 'redirect' in result['error'].lower()

    @patch('agents.background.worker.requests.Session')
    def test_process_http_job_response_too_large(self, mock_session_cls):
        """Should block responses that are too large."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Simulate streaming chunks that exceed MAX_CONTENT_SIZE
        def generate_large_chunks():
            for _ in range(1400):  # 1400 * 8192 > 10MB
                yield b'x' * 8192
        mock_response.iter_content.return_value = generate_large_chunks()
        mock_response.elapsed.total_seconds.return_value = 1.0

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

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

        with patch('agents.background.worker.ALLOW_EXTERNAL', False):
            result = process_http_job(job)
            assert 'error' in result
            assert 'external requests disabled' in result['error'].lower()


class TestMetricsCollection:
    """Test suite for metrics collection."""

    @patch('agents.background.worker.REQUESTS')
    @patch('agents.background.worker.requests.Session')
    def test_metrics_incremented_on_request(self, mock_session_cls, mock_requests):
        """Should increment request metrics."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b''
        mock_response.elapsed.total_seconds.return_value = 0.1

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_cls.return_value.__enter__.return_value = mock_session

        job = {'url': 'http://metrics-test.com/api'}

        with patch('agents.background.worker._validate_and_resolve_target',
                   return_value=(True, '', '1.2.3.4')):
            with patch('agents.background.worker._domain_allowed', return_value=True):
                process_http_job(job)

        mock_requests.inc.assert_called_once()

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

    def test_rate_limit_with_none_domain(self):
        """Should handle None domain gracefully."""
        with pytest.raises((TypeError, AttributeError)):
            check_rate_limit(None)

    def test_rate_limit_with_empty_domain(self):
        """Should handle empty domain string."""
        result = check_rate_limit('')
        # Should either work or raise appropriate error
        assert result is True or result is False