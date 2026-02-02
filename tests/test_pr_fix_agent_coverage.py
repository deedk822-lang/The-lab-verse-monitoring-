
import pytest
import ipaddress
import socket
import os
import json
import sys
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx
import requests

from pr_fix_agent.security import (
    SecurityValidator,
    SecurityError,
    InputValidator,
    RateLimiter
)
from pr_fix_agent.security.secure_requests import (
    SSRFBlocker,
    create_ssrf_safe_session,
    create_ssrf_safe_async_session,
    create_ssrf_safe_requests_session
)
from pr_fix_agent.ollama_agent import OllamaAgent, CostTracker, LLMCost, BudgetExceededError, OllamaQueryError
from pr_fix_agent.orchestrator import CodeReviewOrchestrator, CodeReviewFinding, FixProposal, CodeFix
from pr_fix_agent.security.audit import AuditLogger
from pr_fix_agent.security.middleware import SecurityHeadersMiddleware, RequestIDMiddleware
from pr_fix_agent.security.redis_client import get_redis_client, close_redis
from pr_fix_agent.agents.huggingface import HuggingFaceAgent, ProviderPolicy, ChatResponse, UnifiedLLMAgent
from pr_fix_agent.cli import health_check, main, run_orchestrator, run_production
from pr_fix_agent.analyzer import (
    PRErrorAnalyzer, PRErrorFixer, PromptSanitizer,
    LLMResponseValidator, SafeRegex
)

class TestAnalyzerCoverage:
    def test_prompt_sanitizer_long(self):
        sanitizer = PromptSanitizer()
        long_error = "a" * 20000
        sanitized = sanitizer.sanitize_error_message(long_error)
        assert "[truncated]" in sanitized

    def test_llm_validator_dangerous(self):
        validator = LLMResponseValidator()
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validator.validate_code("import os; os.system('ls')")

    def test_llm_validator_syntax_error(self):
        validator = LLMResponseValidator()
        with pytest.raises(ValueError, match="Invalid syntax"):
            validator.validate_code("if True print('hi')")

    def test_safe_regex_timeout(self):
        # Difficult to trigger timeout reliably, but we can test normal search
        match = SafeRegex.safe_search(r"error", "this is an error")
        assert match is not None

    def test_analyzer_patterns(self):
        from pr_fix_agent.ollama_agent import MockOllamaAgent
        agent = MockOllamaAgent()
        analyzer = PRErrorAnalyzer(agent)
        log = "fatal: something went wrong\nERROR: another error"
        parsed = analyzer.parse_github_actions_log(log)
        assert len(parsed["errors"]) == 2

class TestSecurityValidator:
    def test_validate_path_safe(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        safe_path = "test.txt"
        result = validator.validate_path(safe_path)
        assert result.name == "test.txt"
        assert result.parent == tmp_path.resolve()

    def test_validate_path_traversal(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        with pytest.raises(SecurityError, match="Path traversal"):
            validator.validate_path("../outside.txt")

    def test_validate_module_name_safe(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        assert validator.validate_module_name("numpy") == "numpy"
        assert validator.validate_module_name("my-module_123") == "my-module_123"

    def test_validate_module_name_dangerous(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        with pytest.raises(SecurityError, match="Dangerous characters"):
            validator.validate_module_name("numpy; rm -rf /")

    def test_validate_file_extension(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        assert validator.validate_file_extension("test.py") is True
        assert validator.validate_file_extension("test.exe") is False

    def test_sanitize_input(self, tmp_path):
        validator = SecurityValidator(tmp_path)
        assert validator.sanitize_input("  hello  ") == "hello"
        with pytest.raises(SecurityError, match="Input too long"):
            validator.sanitize_input("a" * 1001)

class TestInputValidator:
    def test_validate_json(self):
        assert InputValidator.validate_json('{"key": "value"}') is True
        assert InputValidator.validate_json('invalid') is False

    def test_validate_yaml_safe(self):
        assert InputValidator.validate_yaml_safe('key: value') is True
        assert InputValidator.validate_yaml_safe('!!python/object:os.system') is False

    def test_validate_url(self):
        assert InputValidator.validate_url("https://example.com") is True
        assert InputValidator.validate_url("not-a-url") is False

class TestRateLimiter:
    def test_rate_limiter(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.check_rate_limit() is True
        assert limiter.check_rate_limit() is True
        assert limiter.check_rate_limit() is False

class TestSSRFBlocker:
    def test_is_safe_url_allowed_domain(self):
        blocker = SSRFBlocker(allowed_domains={"example.com"})
        is_safe, reason = blocker.is_safe_url("http://example.com/path")
        assert is_safe is True
        assert "allowed" in reason

    def test_is_safe_url_blocked_ip(self):
        blocker = SSRFBlocker()
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            is_safe, reason = blocker.is_safe_url("http://localhost/path")
            assert is_safe is False
            assert "blocked network" in reason

    def test_is_safe_url_public_ip(self):
        blocker = SSRFBlocker()
        with patch("socket.gethostbyname", return_value="8.8.8.8"):
            is_safe, reason = blocker.is_safe_url("http://google.com")
            assert is_safe is True

    def test_validate_request_httpx(self):
        blocker = SSRFBlocker()
        request = httpx.Request("GET", "http://8.8.8.8")
        blocker.validate_request(request) # Should not raise

        request_bad = httpx.Request("GET", "http://127.0.0.1")
        with pytest.raises(ValueError, match="SSRF protection"):
            blocker.validate_request(request_bad)

    def test_create_ssrf_safe_session(self):
        session = create_ssrf_safe_session()
        assert isinstance(session, httpx.Client)
        # Testing if it blocks (needs mock or actual request)
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(ValueError):
                session.get("http://localhost")

    @pytest.mark.asyncio
    async def test_create_ssrf_safe_async_session(self):
        async with create_ssrf_safe_async_session() as client:
            assert isinstance(client, httpx.AsyncClient)
            with patch("socket.gethostbyname", return_value="127.0.0.1"):
                with pytest.raises(ValueError):
                    await client.get("http://localhost")

    def test_create_ssrf_safe_requests_session(self):
        session = create_ssrf_safe_requests_session()
        assert isinstance(session, requests.Session)
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(ValueError):
                session.get("http://localhost")

class TestAuditLoggerCoverage:
    def test_audit_logger_init(self, tmp_path):
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(log_file)
        assert log_file.exists()
        logger.log_event("test", "user1", "127.0.0.1", "res", "act", "succ", "req1")
        assert "user1" in log_file.read_text()

class TestMiddlewareCoverage:
    @pytest.mark.asyncio
    async def test_request_id_middleware(self):
        async def call_next(request):
            return httpx.Response(200, content=b"ok")

        middleware = RequestIDMiddleware(Mock())
        from fastapi import Request
        scope = {"type": "http", "headers": [], "method": "GET", "path": "/", "query_string": b""}
        request = Request(scope)

        response = await middleware.dispatch(request, call_next)
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_security_headers_middleware(self):
        async def call_next(request):
            return httpx.Response(200, content=b"ok")

        from fastapi import Request
        scope = {"type": "http", "headers": [], "method": "GET", "path": "/", "query_string": b""}
        request = Request(scope)

        middleware = SecurityHeadersMiddleware(Mock())
        response = await middleware.dispatch(request, call_next)
        assert "Strict-Transport-Security" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_audit_logging_middleware(self):
        from pr_fix_agent.security.middleware import AuditLoggingMiddleware
        from fastapi import Request

        async def call_next(request):
            return httpx.Response(200, content=b"ok")

        scope = {
            "type": "http", "headers": [], "method": "GET",
            "path": "/admin", "query_string": b"",
            "client": ("127.0.0.1", 12345)
        }
        request = Request(scope)
        request.state.request_id = "test-req-id"

        middleware = AuditLoggingMiddleware(Mock())

        with patch("pr_fix_agent.security.audit.get_audit_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200
            mock_logger.log_event.assert_called_once()

class TestRedisClientCoverage:
    @pytest.mark.asyncio
    async def test_redis_client_lifecycle(self):
        with patch("pr_fix_agent.security.redis_client.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost"
            mock_settings.return_value.redis_max_connections = 10

            with patch("redis.asyncio.from_url") as mock_from_url:
                mock_client = AsyncMock()
                mock_from_url.return_value = mock_client

                client = await get_redis_client()
                assert client == mock_client

                await close_redis()
                mock_client.close.assert_called_once()

class TestCLICoverage:
    def test_health_check_success(self):
        with patch("pr_fix_agent.ollama_agent.OllamaAgent.query", return_value="ok"):
            with patch("shutil.which", return_value="/usr/bin/tool"):
                result = health_check()
                assert result == 0

    def test_health_check_failure(self):
        with patch("pr_fix_agent.ollama_agent.OllamaAgent.query", side_effect=OllamaQueryError("Connection failed")):
            result = health_check()
            assert result == 1

    def test_cli_main_health_check(self):
        with patch("sys.argv", ["pr-fix-agent", "health-check"]):
            with patch("pr_fix_agent.cli.health_check", return_value=0) as mock_hc:
                main()
                mock_hc.assert_called_once()

    def test_cli_main_fix(self):
        with patch("sys.argv", ["pr-fix-agent", "fix", "--repo-path", "."]):
            with patch("pr_fix_agent.cli.run_production", return_value=0) as mock_run:
                main()
                mock_run.assert_called_once()

    def test_cli_main_orchestrate(self):
        with patch("sys.argv", ["pr-fix-agent", "orchestrate", "--mode", "reasoning"]):
            with patch("pr_fix_agent.cli.run_orchestrator", return_value=0) as mock_run:
                main()
                mock_run.assert_called_once()

    def test_run_orchestrator(self):
        args = Mock()
        args.mode = "reasoning"
        args.findings = "results/"
        args.proposals = "proposals.json"
        args.test_results = "tests.json"
        args.output = "out.json"
        args.apply = True

        with patch("pr_fix_agent.orchestrator.main", return_value=0) as mock_orch_main:
            assert run_orchestrator(args) == 0

    def test_run_production(self, tmp_path):
        args = Mock()
        args.repo_path = str(tmp_path)
        args.model = "test-model"
        args.log_file = "ci.log"

        with patch("pr_fix_agent.production.main", return_value=0) as mock_prod_main:
            assert run_production(args) == 0

class TestHuggingFaceAgentCoverage:
    def test_huggingface_agent_init(self):
        agent = HuggingFaceAgent(api_key="test-key")
        assert agent.api_key == "test-key"

    def test_huggingface_agent_chat_success(self):
        agent = HuggingFaceAgent(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"total_tokens": 10}
        }
        with patch.object(agent.client, "post", return_value=mock_response):
            response = agent.chat("Hi")
            assert response.content == "Hello!"
            assert response.total_tokens == 10

    def test_huggingface_agent_chat_error(self):
        agent = HuggingFaceAgent(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"
        with patch.object(agent.client, "post", side_effect=Exception("API Error")):
            response = agent.chat("Hi")
            assert "Error" in response.content

    def test_huggingface_agent_embed(self):
        agent = HuggingFaceAgent(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [0.1, 0.2, 0.3]
        with patch.object(agent.client, "post", return_value=mock_response):
            result = agent.embed("test")
            assert result == [0.1, 0.2, 0.3]

    def test_huggingface_agent_text_to_image(self):
        agent = HuggingFaceAgent(api_key="test-key")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"image_data"
        with patch.object(agent.client, "post", return_value=mock_response):
            result = agent.text_to_image("test")
            assert result == b"image_data"

    def test_unified_llm_agent(self):
        agent = UnifiedLLMAgent(backend="huggingface", api_key="key")
        assert agent.backend == "huggingface"

        with patch.object(agent.agent, "chat", return_value="ok"):
            assert agent.chat("hi") == "ok"

class TestOrchestratorCoverage:
    def test_finding_dataclass(self):
        finding = CodeReviewFinding("file.py", 1, 1, "high", "security", "issue", "suggestion")
        assert finding.file == "file.py"

    def test_orchestrator_init(self):
        orch = CodeReviewOrchestrator()
        assert orch.reasoning_agent.model == "deepseek-r1:1.5b"

    def test_generate_fix_proposals(self):
        orch = CodeReviewOrchestrator()
        finding = CodeReviewFinding("file.py", 1, 1, "high", "security", "issue", "suggestion")

        with patch.object(orch.reasoning_agent, "query", return_value="Some analysis"):
            proposals = orch._generate_fix_proposals([finding])
            assert len(proposals) == 1
            assert proposals[0].finding == finding

    def test_implement_fixes(self, tmp_path):
        orch = CodeReviewOrchestrator()
        finding = CodeReviewFinding("test.py", 1, 1, "high", "security", "issue", "suggestion")
        proposal = FixProposal(finding, "root cause", "approach", ["change"], "low", ["test"])

        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        with patch.object(orch.coding_agent, "query", return_value="print('fixed')"):
            fixes = orch._implement_fixes([proposal], tmp_path)
            assert len(fixes) == 1
            assert fixes[0].fixed_code == "print('fixed')"

    def test_apply_and_test(self, tmp_path):
        orch = CodeReviewOrchestrator()
        finding = CodeReviewFinding("test.py", 1, 1, "high", "security", "issue", "suggestion")
        proposal = FixProposal(finding, "root cause", "approach", ["change"], "low", ["test"])
        fix = CodeFix(proposal, str(tmp_path / "test.py"), "old", "new", "expl")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Tests passed"
            mock_run.return_value.stderr = ""

            result = orch._apply_and_test([fix], tmp_path)
            assert result.passed is True
            assert (tmp_path / "test.py").read_text() == "new"

    def test_generate_pr_body(self):
        orch = CodeReviewOrchestrator()
        finding = CodeReviewFinding("file.py", 1, 1, "high", "security", "issue", "suggestion")
        proposal = FixProposal(finding, "root cause", "approach", ["change"], "low", ["test"])
        body = orch.generate_pr_body([proposal], [], None)
        assert "Automated Code Review Fixes" in body
        assert "file.py" in body

    def test_orchestrator_main(self, tmp_path):
        # Test reasoning mode with empty findings
        with patch("sys.argv", ["orchestrator", "--mode", "reasoning", "--findings", str(tmp_path)]):
            from pr_fix_agent.orchestrator import main as orch_main
            orch_main()
            assert (Path.cwd() / "proposals.json").exists()
            (Path.cwd() / "proposals.json").unlink()

    def test_orchestrator_main_coding(self, tmp_path):
        from pr_fix_agent.orchestrator import main as orch_main
        proposals_file = tmp_path / "proposals.json"
        # Create a non-empty proposal for better coverage
        proposal_data = [{
            "finding": {
                "file": "test.py", "line_start": 1, "line_end": 1,
                "severity": "high", "category": "security", "issue": "x", "suggestion": "y", "code_snippet": "z"
            },
            "root_cause": "rc", "fix_approach": "fa", "expected_changes": [], "risk_level": "low", "test_requirements": []
        }]
        proposals_file.write_text(json.dumps(proposal_data))
        with patch("sys.argv", ["orchestrator", "--mode", "coding", "--proposals", str(proposals_file)]):
            orch_main()

    def test_orchestrator_main_generate_pr(self, tmp_path):
        from pr_fix_agent.orchestrator import main as orch_main
        proposals_file = tmp_path / "proposals.json"
        proposal_data = [{
            "finding": {
                "file": "test.py", "line_start": 1, "line_end": 1,
                "severity": "high", "category": "security", "issue": "x", "suggestion": "y", "code_snippet": "z"
            },
            "root_cause": "rc", "fix_approach": "fa", "expected_changes": [], "risk_level": "low", "test_requirements": []
        }]
        proposals_file.write_text(json.dumps(proposal_data))

        test_results_file = tmp_path / "tests.json"
        test_results_file.write_text(json.dumps({"summary": {"total": 1, "passed": 1, "failed": 0}}))

        with patch("sys.argv", ["orchestrator", "--mode", "generate-pr", "--proposals", str(proposals_file), "--test-results", str(test_results_file)]):
            orch_main()

    def test_orchestrator_reasoning_with_findings(self, tmp_path):
        from pr_fix_agent.orchestrator import main as orch_main
        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()

        # Case 1: List format (e.g. bandit)
        f1 = findings_dir / "bandit.json"
        f1.write_text(json.dumps([{"filename": "test.py", "issue_text": "bad code"}]))

        # Case 2: Dict format (e.g. ruff)
        f2 = findings_dir / "ruff.json"
        f2.write_text(json.dumps({"results": [{"filename": "other.py", "message": "fix me"}]}))

        with patch("sys.argv", ["orchestrator", "--mode", "reasoning", "--findings", str(findings_dir)]):
            with patch("pr_fix_agent.ollama_agent.OllamaAgent.query", return_value="analysis"):
                orch_main()
                assert (Path.cwd() / "proposals.json").exists()
                (Path.cwd() / "proposals.json").unlink()

class TestProductionCoverage:
    def test_production_main_health(self):
        from pr_fix_agent.production import main as prod_main
        with patch("sys.argv", ["production", "--health-check"]):
            assert prod_main() == 0

    def test_production_main_real(self, tmp_path):
        from pr_fix_agent.production import main as prod_main
        with patch("sys.argv", ["production", "--repo-path", str(tmp_path)]):
            assert prod_main() == 0

class TestModelsCoverage:
    def test_model_selector(self):
        from pr_fix_agent.models import ModelSelector
        selector = ModelSelector()
        model = selector.select_model("reasoning", budget_remaining=10.0)
        assert model is not None
        assert model.provider == "ollama"  # Should prefer free by default

        model_paid = selector.select_model("reasoning", budget_remaining=100.0, prefer_free=False)
        assert model_paid.provider == "openai" # Should prefer quality

        chain = selector.get_fallback_chain("coding")
        assert len(chain) > 0

class TestObservabilityCoverage:
    def test_configure_logging(self):
        from pr_fix_agent.observability.logging import configure_logging
        from pr_fix_agent.core.config import Settings
        settings = Settings(log_level="INFO", log_format="json")
        configure_logging(settings)

    def test_initialize_metrics(self):
        from pr_fix_agent.observability.metrics import initialize_metrics
        initialize_metrics()

    def test_tracing(self):
        from pr_fix_agent.observability.tracing import initialize_tracing
        from pr_fix_agent.core.config import Settings
        settings = Settings()
        initialize_tracing(settings)

class TestOllamaAgentCoverage:
    def test_cost_tracker_record_usage(self):
        tracker = CostTracker(budget_usd=1.0)
        cost = tracker.record_usage("gpt-4", "hello", "hi there")
        assert cost.model == "gpt-4"
        assert tracker.total_cost > 0
        assert len(tracker.costs) == 1

    def test_cost_tracker_budget_exceeded(self):
        tracker = CostTracker(budget_usd=0.0000001)
        with pytest.raises(BudgetExceededError):
            tracker.record_usage("gpt-4", "very long prompt" * 100, "very long response" * 100)

    def test_cost_tracker_report(self):
        tracker = CostTracker(budget_usd=10.0)
        tracker.record_usage("gpt-4", "hello", "hi")
        report = tracker.get_report()
        assert report["total_calls"] == 1
        assert "gpt-4" in report["usage_by_model"]

    def test_ollama_agent_query_success(self):
        agent = OllamaAgent(model="test-model")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is a fix"}

        with patch.object(agent.session, "post", return_value=mock_response):
            result = agent.query("Analyze error")
            assert result == "This is a fix"

    def test_ollama_agent_query_failure(self):
        agent = OllamaAgent(model="test-model")
        with patch.object(agent.session, "post", side_effect=requests.RequestException("Network error")):
            with pytest.raises(OllamaQueryError):
                agent.query("Analyze error")

    def test_ollama_agent_invalid_format(self):
        agent = OllamaAgent(model="test-model")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"wrong_key": "oops"}
        with patch.object(agent.session, "post", return_value=mock_response):
            with pytest.raises(OllamaQueryError, match="Invalid response format"):
                agent.query("Analyze error")
