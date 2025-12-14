#!/usr/bin/env python3
"""
Tests for LocalAI Fallback and Resilience System
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCircuitBreaker(unittest.TestCase):
    """Test Circuit Breaker Pattern"""

    def setUp(self):
        """Setup test fixtures"""
        from services.localai_fallback import CircuitBreaker
        self.breaker = CircuitBreaker(failure_threshold=3, timeout=1)

    def test_circuit_closed_initially(self):
        """Test circuit starts closed"""
        self.assertEqual(self.breaker.state, "CLOSED")
        self.assertEqual(self.breaker.failure_count, 0)

    def test_successful_call(self):
        """Test successful call keeps circuit closed"""
        def success_func():
            return "success"

        result = self.breaker.call(success_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.breaker.state, "CLOSED")
        self.assertEqual(self.breaker.failure_count, 0)

    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold"""
        def failing_func():
            raise Exception("Failure")

        # Trigger failures
        for i in range(3):
            try:
                self.breaker.call(failing_func)
            except Exception:
                pass

        self.assertEqual(self.breaker.state, "OPEN")
        self.assertEqual(self.breaker.failure_count, 3)

    def test_circuit_prevents_calls_when_open(self):
        """Test circuit breaker prevents calls when open"""
        def failing_func():
            raise Exception("Failure")

        # Open the circuit
        for i in range(3):
            try:
                self.breaker.call(failing_func)
            except Exception:
                pass

        # Try to call again - should be blocked
        with self.assertRaises(Exception) as context:
            self.breaker.call(failing_func)

        self.assertIn("Circuit breaker OPEN", str(context.exception))

    def test_circuit_half_open_after_timeout(self):
        """Test circuit moves to half-open after timeout"""
        def failing_func():
            raise Exception("Failure")

        # Open the circuit
        for i in range(3):
            try:
                self.breaker.call(failing_func)
            except Exception:
                pass

        # Wait for timeout
        time.sleep(1.1)

        # Next call should attempt (half-open)
        # This will fail and stay open, but state should change first
        try:
            self.breaker.call(failing_func)
        except Exception:
            pass


class TestLocalAIClient(unittest.TestCase):
    """Test LocalAI Client"""

    def setUp(self):
        """Setup test fixtures"""
        from services.localai_fallback import LocalAIClient
        self.client = LocalAIClient(base_url="http://localhost:8080")

    def test_init(self):
        """Test client initialization"""
        self.assertEqual(self.client.base_url, "http://localhost:8080")
        self.assertEqual(self.client.timeout, 30)

    @patch('requests.get')
    def test_check_availability_success(self, mock_get):
        """Test availability check when server is running"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        from services.localai_fallback import LocalAIClient
        client = LocalAIClient()
        # Availability is checked in __init__
        mock_get.assert_called()

    @patch('requests.get')
    def test_check_availability_failure(self, mock_get):
        """Test availability check when server is down"""
        mock_get.side_effect = Exception("Connection refused")

        from services.localai_fallback import LocalAIClient
        client = LocalAIClient()
        self.assertFalse(client.available)

    @patch('requests.get')
    def test_list_models(self, mock_get):
        """Test listing available models"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-3.5-turbo"},
                {"id": "text-embedding-ada-002"}
            ]
        }
        mock_get.return_value = mock_response

        from services.localai_fallback import LocalAIClient
        client = LocalAIClient()
        client.available = True  # Force available

        models = client.list_models()
        self.assertEqual(len(models), 2)
        self.assertIn("gpt-3.5-turbo", models)

    @patch('requests.post')
    def test_chat_completion(self, mock_post):
        """Test chat completion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Test response"}}
            ]
        }
        mock_post.return_value = mock_response

        from services.localai_fallback import LocalAIClient
        client = LocalAIClient()
        client.available = True

        result = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )

        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "Test response")

    @patch('requests.post')
    def test_embeddings(self, mock_post):
        """Test embeddings generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]}
            ]
        }
        mock_post.return_value = mock_response

        from services.localai_fallback import LocalAIClient
        client = LocalAIClient()
        client.available = True

        result = client.embeddings(["test text"])

        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 1)


class TestResilientAIService(unittest.TestCase):
    """Test Resilient AI Service"""

    def setUp(self):
        """Setup test fixtures"""
        from services.localai_fallback import ResilientAIService

        # Mock environment
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

        self.service = ResilientAIService()

    def tearDown(self):
        """Cleanup"""
        self.env_patcher.stop()

    def test_init_without_keys(self):
        """Test initialization without API keys"""
        self.assertNotIn('cohere', self.service.providers)
        self.assertNotIn('mistral', self.service.providers)
        # Should have mock as fallback
        self.assertIn('mock', self.service.provider_priority)

    def test_init_with_keys(self):
        """Test initialization with API keys"""
        with patch.dict(os.environ, {
            'COHERE_API_KEY': 'test_key',
            'MISTRAL_API_KEY': 'test_key'
        }):
            from services.localai_fallback import ResilientAIService
            service = ResilientAIService()
            # May or may not initialize depending on SDK availability
            self.assertIsNotNone(service.provider_priority)

    def test_provider_priority(self):
        """Test provider priority determination"""
        priorities = self.service.provider_priority
        self.assertIsInstance(priorities, list)
        self.assertGreater(len(priorities), 0)
        # Mock should always be last
        self.assertEqual(priorities[-1], 'mock')

    def test_generate_text_mock_mode(self):
        """Test text generation in mock mode"""
        result = self.service.generate_text("Test prompt")

        self.assertIn("text", result)
        self.assertIn("provider", result)
        self.assertEqual(result["provider"], "mock")
        self.assertTrue(result.get("mock", False))

    def test_generate_text_with_preferred_provider(self):
        """Test generation with preferred provider"""
        result = self.service.generate_text(
            "Test prompt",
            preferred_provider="mock"
        )

        self.assertEqual(result["provider"], "mock")

    def test_generate_embeddings_mock_mode(self):
        """Test embeddings generation in mock mode"""
        result = self.service.generate_embeddings(["text1", "text2"])

        self.assertIn("embeddings", result)
        self.assertEqual(len(result["embeddings"]), 2)
        self.assertTrue(result.get("mock", False))

    def test_fallback_cascade(self):
        """Test that fallback cascades through providers"""
        # All providers should fail, ending in mock
        result = self.service.generate_text("Test")

        # Should eventually return mock response
        self.assertIn("provider", result)
        self.assertIn("text", result)

    def test_health_status(self):
        """Test health status reporting"""
        status = self.service.get_health_status()

        self.assertIn("timestamp", status)
        self.assertIn("providers", status)
        self.assertIn("recommended_provider", status)

    @patch('services.localai_fallback.ResilientAIService._generate_cohere')
    def test_cohere_generation(self, mock_generate_cohere):
        """Test generation with Cohere"""
        mock_generate_cohere.return_value = {
            "text": "Generated text",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }

        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from services.localai_fallback import ResilientAIService
            service = ResilientAIService()

            if 'cohere' in service.providers:
                result = service.generate_text("Test", preferred_provider='cohere')
                self.assertIn("text", result)
                self.assertEqual(result["text"], "Generated text")


class TestLocalAISetup(unittest.TestCase):
    """Test LocalAI Setup Helper"""

    def test_get_docker_command_basic(self):
        """Test basic Docker command generation"""
        from services.localai_fallback import LocalAISetup

        cmd = LocalAISetup.get_docker_command()

        self.assertIn("docker run", cmd)
        self.assertIn("-p 8080:8080", cmd)
        self.assertIn("localai/localai:latest", cmd)

    def test_get_docker_command_custom_port(self):
        """Test Docker command with custom port"""
        from services.localai_fallback import LocalAISetup

        cmd = LocalAISetup.get_docker_command(port=9090)

        self.assertIn("-p 9090:8080", cmd)

    def test_get_docker_command_with_models(self):
        """Test Docker command with model specification"""
        from services.localai_fallback import LocalAISetup

        cmd = LocalAISetup.get_docker_command(
            models=["gpt-3.5-turbo", "text-embedding-ada-002"]
        )

        self.assertIn("--models", cmd)

    def test_install_instructions(self):
        """Test installation instructions"""
        from services.localai_fallback import LocalAISetup

        instructions = LocalAISetup.install_instructions()

        self.assertIn("Docker", instructions)
        self.assertIn("docker run", instructions)
        self.assertIn("Kubernetes", instructions)


class TestIntegration(unittest.TestCase):
    """Integration tests for fallback system"""

    def test_end_to_end_generation(self):
        """Test complete generation workflow with fallback"""
        from services.localai_fallback import ResilientAIService

        with patch.dict(os.environ, {}, clear=True):
            service = ResilientAIService()

            # Generate text (should fall back to mock)
            result = service.generate_text("Write a greeting")

            self.assertIn("text", result)
            self.assertIn("provider", result)
            self.assertIn("usage", result)

    def test_multiple_requests_with_circuit_breaker(self):
        """Test circuit breaker behavior with multiple requests"""
        from services.localai_fallback import ResilientAIService

        service = ResilientAIService()

        # Make multiple requests
        results = []
        for i in range(5):
            result = service.generate_text(f"Test {i}")
            results.append(result)

        # All should succeed (with mock)
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIn("text", result)

    def test_embedding_generation_cascade(self):
        """Test embedding generation with provider cascade"""
        from services.localai_fallback import ResilientAIService

        service = ResilientAIService()

        result = service.generate_embeddings(
            ["text1", "text2", "text3"]
        )

        self.assertIn("embeddings", result)
        self.assertEqual(len(result["embeddings"]), 3)


def run_localai_fallback_tests():
    """Run all LocalAI fallback tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreaker))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalAIClient))
    suite.addTests(loader.loadTestsFromTestCase(TestResilientAIService))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalAISetup))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("LOCALAI FALLBACK & RESILIENCE TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_localai_fallback_tests() else 1)
