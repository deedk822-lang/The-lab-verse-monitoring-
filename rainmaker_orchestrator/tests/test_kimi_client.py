"""
Comprehensive unit tests for KimiClient.

Tests cover initialization, content generation, health checks,
error handling, and various edge cases.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import os
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
from rainmaker_orchestrator.clients.kimi import KimiClient


class TestKimiClientInitialization:
    """Test suite for KimiClient initialization."""
    
    def test_init_with_default_values(self):
        """Should initialize with default environment values."""
        with patch.dict(os.environ, {
            'KIMI_API_BASE': 'http://test-base:8000/v1',
            'KIMI_API_KEY': 'test-key',
            'KIMI_MODEL': 'test-model'
        }):
            with patch('rainmaker_orchestrator.clients.kimi.OpenAI') as mock_openai:
                client = KimiClient()
                
                mock_openai.assert_called_once_with(
                    base_url='http://test-base:8000/v1',
                    api_key='test-key'
                )
                assert client.model == 'test-model'
    
    def test_init_with_custom_api_key(self):
        """Should use provided API key over environment variable."""
        with patch.dict(os.environ, {'KIMI_API_KEY': 'env-key'}):
            with patch('rainmaker_orchestrator.clients.kimi.OpenAI') as mock_openai:
                client = KimiClient(api_key='custom-key')
                
                call_args = mock_openai.call_args
                assert call_args[1]['api_key'] == 'custom-key'
    
    def test_init_with_missing_env_vars(self):
        """Should use default fallback values when env vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('rainmaker_orchestrator.clients.kimi.OpenAI') as mock_openai:
                client = KimiClient()
                
                call_args = mock_openai.call_args
                assert call_args[1]['base_url'] == 'http://kimi-linear:8000/v1'
                assert call_args[1]['api_key'] == 'EMPTY'
                assert client.model == 'moonshot-v1-8k'
    
    def test_init_with_empty_api_key_env(self):
        """Should fall back to 'EMPTY' when API key env var is empty."""
        with patch.dict(os.environ, {'KIMI_API_KEY': ''}):
            with patch('rainmaker_orchestrator.clients.kimi.OpenAI') as mock_openai:
                client = KimiClient()
                
                call_args = mock_openai.call_args
                assert call_args[1]['api_key'] == 'EMPTY'


class TestKimiClientGenerate:
    """Test suite for content generation functionality."""
    
    def setup_method(self):
        """
        Prepare a mocked OpenAI client and initialize a KimiClient instance that uses it.
        
        Creates a Mock conforming to the OpenAI spec, patches
        rainmaker_orchestrator.clients.kimi.OpenAI to return that mock, and constructs
        a KimiClient with api_key 'test-key' so subsequent tests interact with the mock.
        """
        self.mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=self.mock_openai_client):
            self.client = KimiClient(api_key='test-key')
    
    def test_generate_success_general_mode(self):
        """Should generate content successfully in general mode."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Generated response'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Act
        result = self.client.generate('Test prompt', mode='general')
        
        # Assert
        assert result == 'Generated response'
        
        call_args = self.mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'moonshot-v1-8k'
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['timeout'] == 30.0
        
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert 'Kimi' in messages[0]['content']
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'Test prompt'
    
    def test_generate_success_hotfix_mode(self):
        """Should generate content with hotfix-specific settings."""
        # Arrange
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Hotfix code'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Act
        result = self.client.generate('Fix this bug', mode='hotfix')
        
        # Assert
        assert result == 'Hotfix code'
        
        call_args = self.mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.3  # Lower temperature for hotfix
        
        messages = call_args[1]['messages']
        assert 'site reliability engineer' in messages[0]['content'].lower()
        assert 'patch' in messages[0]['content'].lower()
    
    def test_generate_with_empty_prompt(self):
        """Should handle empty prompt."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response to empty prompt'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate('', mode='general')
        
        assert result == 'Response to empty prompt'
    
    def test_generate_with_very_long_prompt(self):
        """Should handle very long prompts."""
        long_prompt = 'A' * 100000
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate(long_prompt)
        
        assert result == 'Response'
        call_args = self.mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['messages'][1]['content'] == long_prompt
    
    def test_generate_api_error(self):
        """Should return None on API error."""
        self.mock_openai_client.chat.completions.create.side_effect = APIError(
            message='API Error',
            request=Mock(),
            body=None
        )
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_timeout_error(self):
        """Should return None on timeout."""
        self.mock_openai_client.chat.completions.create.side_effect = APITimeoutError(
            request=Mock()
        )
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_connection_error(self):
        """Should return None on connection error."""
        self.mock_openai_client.chat.completions.create.side_effect = APIConnectionError(
            message='Connection failed',
            request=Mock()
        )
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_generic_exception(self):
        """Should return None on unexpected exception."""
        self.mock_openai_client.chat.completions.create.side_effect = Exception('Unexpected error')
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_empty_choices(self):
        """Should return None when API returns empty choices."""
        mock_response = Mock()
        mock_response.choices = []
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_none_content(self):
        """Should return None when message content is None."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_empty_string_content(self):
        """Should return None when message content is empty string."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ''
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate('Test prompt')
        
        assert result is None
    
    def test_generate_with_special_characters(self):
        """Should handle special characters in prompt."""
        prompt = 'Test with "quotes", \'apostrophes\', and\nnewlines\t\ttabs'
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate(prompt)
        
        assert result == 'Response'
    
    def test_generate_with_unicode(self):
        """Should handle Unicode characters."""
        prompt = 'Test with émojis 😀 and 中文字符'
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Unicode response 你好'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate(prompt)
        
        assert result == 'Unicode response 你好'
    
    def test_generate_multiple_choices(self):
        """Should return first choice when multiple choices exist."""
        mock_response = Mock()
        mock_response.choices = [Mock(), Mock()]
        mock_response.choices[0].message.content = 'First choice'
        mock_response.choices[1].message.content = 'Second choice'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = self.client.generate('Test prompt')
        
        assert result == 'First choice'
    
    def test_generate_preserves_model_setting(self):
        """Should use configured model for generation."""
        with patch.dict(os.environ, {'KIMI_MODEL': 'custom-model-v2'}):
            with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=self.mock_openai_client):
                client = KimiClient()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response'
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        client.generate('Test')
        
        call_args = self.mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'custom-model-v2'


class TestKimiClientHealthCheck:
    """Test suite for health check functionality."""
    
    def setup_method(self):
        """
        Prepare a mocked OpenAI client and initialize a KimiClient instance that uses it.
        
        Creates a Mock conforming to the OpenAI spec, patches
        rainmaker_orchestrator.clients.kimi.OpenAI to return that mock, and constructs
        a KimiClient with api_key 'test-key' so subsequent tests interact with the mock.
        """
        self.mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=self.mock_openai_client):
            self.client = KimiClient(api_key='test-key')
    
    def test_health_check_success(self):
        """Should return True when API is healthy."""
        self.mock_openai_client.models.list.return_value = Mock()
        
        result = self.client.health_check()
        
        assert result is True
        self.mock_openai_client.models.list.assert_called_once()
    
    def test_health_check_api_error(self):
        """Should return False on API error."""
        self.mock_openai_client.models.list.side_effect = APIError(
            message='API Error',
            request=Mock(),
            body=None
        )
        
        result = self.client.health_check()
        
        assert result is False
    
    def test_health_check_connection_error(self):
        """Should return False on connection error."""
        self.mock_openai_client.models.list.side_effect = APIConnectionError(
            message='Connection failed',
            request=Mock()
        )
        
        result = self.client.health_check()
        
        assert result is False
    
    def test_health_check_timeout(self):
        """Should return False on timeout."""
        self.mock_openai_client.models.list.side_effect = APITimeoutError(
            request=Mock()
        )
        
        result = self.client.health_check()
        
        assert result is False
    
    def test_health_check_generic_exception(self):
        """Should return False on unexpected exception."""
        self.mock_openai_client.models.list.side_effect = Exception('Unexpected error')
        
        result = self.client.health_check()
        
        assert result is False
    
    def test_health_check_multiple_calls(self):
        """Should handle multiple consecutive health checks."""
        self.mock_openai_client.models.list.return_value = Mock()
        
        results = [self.client.health_check() for _ in range(5)]
        
        assert all(results)
        assert self.mock_openai_client.models.list.call_count == 5


class TestKimiClientEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    def test_generate_with_none_mode(self):
        """Should handle None mode parameter."""
        mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=mock_openai_client):
            client = KimiClient()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Should default to general mode (temperature 0.7)
        result = client.generate('Test', mode=None)
        
        call_args = mock_openai_client.chat.completions.create.call_args
        # When mode is None, it won't equal 'hotfix', so temperature should be 0.7
        assert call_args[1]['temperature'] == 0.7
    
    def test_generate_with_invalid_mode(self):
        """Should handle invalid mode parameter."""
        mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=mock_openai_client):
            client = KimiClient()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Response'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = client.generate('Test', mode='invalid_mode')
        
        # Should default to general mode settings
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.7
    
    def test_concurrent_generation_requests(self):
        """Should handle multiple concurrent generation requests."""
        mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=mock_openai_client):
            client = KimiClient()
        
        mock_openai_client.chat.completions.create.side_effect = [
            Mock(choices=[Mock(message=Mock(content=f'Response {i}'))]) 
            for i in range(10)
        ]
        
        prompts = [f'Prompt {i}' for i in range(10)]
        results = [client.generate(p) for p in prompts]
        
        assert len(results) == 10
        assert all(r is not None for r in results)
        assert mock_openai_client.chat.completions.create.call_count == 10


class TestKimiClientIntegration:
    """Integration-style tests for realistic scenarios."""
    
    def test_realistic_code_generation_flow(self):
        """Should handle realistic code generation workflow."""
        mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=mock_openai_client):
            client = KimiClient()
        
        # Simulate successful code generation
        code_response = '''
def calculate_total(items):
    """Calculate total price of items."""
    return sum(item.price for item in items)
'''
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = code_response
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = client.generate(
            'Generate a Python function to calculate total price',
            mode='general'
        )
        
        assert result == code_response
        assert 'def calculate_total' in result
    
    def test_realistic_error_recovery_flow(self):
        """Should handle realistic error recovery scenario."""
        mock_openai_client = Mock(spec=OpenAI)
        with patch('rainmaker_orchestrator.clients.kimi.OpenAI', return_value=mock_openai_client):
            client = KimiClient()
        
        # First attempt fails
        mock_openai_client.chat.completions.create.side_effect = [
            APITimeoutError(request=Mock()),
            Mock(choices=[Mock(message=Mock(content='Recovery successful'))])
        ]
        
        # First call fails
        result1 = client.generate('Test prompt')
        assert result1 is None
        
        # Second call succeeds
        mock_openai_client.chat.completions.create.side_effect = None
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content='Success'))]
        )
        result2 = client.generate('Test prompt')
        assert result2 == 'Success'