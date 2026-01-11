"""
Unit tests for configuration management.

Tests cover settings initialization, environment variable loading,
and default value handling.
"""
import pytest
import os
from unittest.mock import patch
from rainmaker_orchestrator.config import Settings, settings


class TestSettingsInitialization:
    """Test suite for Settings class initialization."""
    
    def test_init_with_all_env_vars(self):
        """Should load all settings from environment variables."""
        env_vars = {
            'LOG_LEVEL': 'DEBUG',
            'WORKSPACE_PATH': '/custom/workspace',
            'ENVIRONMENT': 'development',
            'KIMI_API_KEY': 'test-api-key-123',
            'KIMI_API_BASE': 'https://custom-kimi.api/v1',
            'OLLAMA_API_BASE': 'http://custom-ollama:12345/api'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            assert test_settings.log_level == 'DEBUG'
            assert test_settings.workspace_path == '/custom/workspace'
            assert test_settings.environment == 'development'
            assert test_settings.kimi_api_key == 'test-api-key-123'
            assert test_settings.kimi_api_base == 'https://custom-kimi.api/v1'
            assert test_settings.ollama_api_base == 'http://custom-ollama:12345/api'
    
    def test_init_with_default_values(self):
        """Should use default values when env vars are not set."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            
            assert test_settings.log_level == 'INFO'
            assert test_settings.workspace_path == '/workspace'
            assert test_settings.environment == 'production'
            assert test_settings.kimi_api_key is None
            assert test_settings.kimi_api_base == 'https://api.moonshot.ai/v1'
            assert test_settings.ollama_api_base == 'http://localhost:11434/api'
    
    def test_init_with_partial_env_vars(self):
        """Should use mix of env vars and defaults."""
        env_vars = {
            'LOG_LEVEL': 'WARNING',
            'KIMI_API_KEY': 'partial-key'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            assert test_settings.log_level == 'WARNING'
            assert test_settings.kimi_api_key == 'partial-key'
            # Defaults for others
            assert test_settings.workspace_path == '/workspace'
            assert test_settings.environment == 'production'
    
    def test_init_with_empty_string_values(self):
        """Should treat empty strings as empty, not as defaults."""
        env_vars = {
            'KIMI_API_KEY': '',
            'LOG_LEVEL': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            # Empty string should override default for optional fields
            assert test_settings.kimi_api_key == ''
            assert test_settings.log_level == ''  # Empty, not 'INFO'


class TestSettingsLogLevel:
    """Test suite for log level configuration."""
    
    @pytest.mark.parametrize('log_level', ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    def test_valid_log_levels(self, log_level):
        """Should accept standard Python log levels."""
        with patch.dict(os.environ, {'LOG_LEVEL': log_level}, clear=True):
            test_settings = Settings()
            assert test_settings.log_level == log_level
    
    def test_lowercase_log_level(self):
        """Should preserve case of log level."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'debug'}, clear=True):
            test_settings = Settings()
            assert test_settings.log_level == 'debug'
    
    def test_mixed_case_log_level(self):
        """Should preserve mixed case log level."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DeBuG'}, clear=True):
            test_settings = Settings()
            assert test_settings.log_level == 'DeBuG'


class TestSettingsWorkspacePath:
    """Test suite for workspace path configuration."""
    
    def test_absolute_workspace_path(self):
        """Should accept absolute workspace path."""
        with patch.dict(os.environ, {'WORKSPACE_PATH': '/absolute/path/workspace'}, clear=True):
            test_settings = Settings()
            assert test_settings.workspace_path == '/absolute/path/workspace'
    
    def test_relative_workspace_path(self):
        """Should accept relative workspace path."""
        with patch.dict(os.environ, {'WORKSPACE_PATH': './relative/workspace'}, clear=True):
            test_settings = Settings()
            assert test_settings.workspace_path == './relative/workspace'
    
    def test_workspace_path_with_spaces(self):
        """Should handle workspace paths with spaces."""
        with patch.dict(os.environ, {'WORKSPACE_PATH': '/path/with spaces/workspace'}, clear=True):
            test_settings = Settings()
            assert test_settings.workspace_path == '/path/with spaces/workspace'


class TestSettingsEnvironment:
    """Test suite for environment configuration."""
    
    @pytest.mark.parametrize('env', ['production', 'development', 'staging', 'test'])
    def test_common_environment_values(self, env):
        """Should accept common environment values."""
        with patch.dict(os.environ, {'ENVIRONMENT': env}, clear=True):
            test_settings = Settings()
            assert test_settings.environment == env
    
    def test_custom_environment_value(self):
        """Should accept custom environment value."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'custom-env'}, clear=True):
            test_settings = Settings()
            assert test_settings.environment == 'custom-env'


class TestSettingsAPIConfiguration:
    """Test suite for API-related configuration."""
    
    def test_kimi_api_key_with_value(self):
        """Should store Kimi API key when provided."""
        with patch.dict(os.environ, {'KIMI_API_KEY': 'sk-1234567890'}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_key == 'sk-1234567890'
    
    def test_kimi_api_key_none_when_missing(self):
        """Should set Kimi API key to None when not provided."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_key is None
    
    def test_kimi_api_base_custom(self):
        """Should use custom Kimi API base URL."""
        with patch.dict(os.environ, {'KIMI_API_BASE': 'https://custom.api/v2'}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_base == 'https://custom.api/v2'
    
    def test_kimi_api_base_default(self):
        """Should use default Kimi API base URL."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_base == 'https://api.moonshot.ai/v1'
    
    def test_ollama_api_base_custom(self):
        """Should use custom Ollama API base URL."""
        with patch.dict(os.environ, {'OLLAMA_API_BASE': 'http://ollama-server:9999/api'}, clear=True):
            test_settings = Settings()
            assert test_settings.ollama_api_base == 'http://ollama-server:9999/api'
    
    def test_ollama_api_base_default(self):
        """Should use default Ollama API base URL."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.ollama_api_base == 'http://localhost:11434/api'


class TestSettingsModule:
    """Test suite for module-level settings instance."""
    
    def test_settings_instance_exists(self):
        """Should provide a module-level settings instance."""
        from rainmaker_orchestrator.config import settings
        
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_settings_instance_attributes(self):
        """Should have all expected attributes."""
        from rainmaker_orchestrator.config import settings
        
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'workspace_path')
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'kimi_api_key')
        assert hasattr(settings, 'kimi_api_base')
        assert hasattr(settings, 'ollama_api_base')


class TestSettingsEdgeCases:
    """Test suite for edge cases and special scenarios."""
    
    def test_very_long_api_key(self):
        """Should handle very long API keys."""
        long_key = 'sk-' + 'x' * 1000
        with patch.dict(os.environ, {'KIMI_API_KEY': long_key}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_key == long_key
    
    def test_special_characters_in_paths(self):
        """Should handle special characters in paths."""
        with patch.dict(os.environ, {'WORKSPACE_PATH': '/path/with/special-chars_123/@test'}, clear=True):
            test_settings = Settings()
            assert test_settings.workspace_path == '/path/with/special-chars_123/@test'
    
    def test_unicode_in_environment_value(self):
        """Should handle Unicode in environment value."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'test-环境'}, clear=True):
            test_settings = Settings()
            assert test_settings.environment == 'test-环境'
    
    def test_url_with_auth_in_api_base(self):
        """Should handle URLs with authentication in API base."""
        with patch.dict(os.environ, {'KIMI_API_BASE': 'https://user:pass@api.example.com/v1'}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_base == 'https://user:pass@api.example.com/v1'
    
    def test_whitespace_in_env_vars(self):
        """Should preserve whitespace in environment variables."""
        with patch.dict(os.environ, {'LOG_LEVEL': '  INFO  '}, clear=True):
            test_settings = Settings()
            # The value should be preserved as-is (including whitespace)
            assert test_settings.log_level == '  INFO  '


class TestSettingsTypeAnnotations:
    """Test suite for type hints and annotations."""
    
    def test_log_level_type(self):
        """Should have correct type for log_level."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'INFO'}, clear=True):
            test_settings = Settings()
            assert isinstance(test_settings.log_level, str)
    
    def test_workspace_path_type(self):
        """Should have correct type for workspace_path."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert isinstance(test_settings.workspace_path, str)
    
    def test_environment_type(self):
        """Should have correct type for environment."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert isinstance(test_settings.environment, str)
    
    def test_kimi_api_key_optional_type(self):
        """Should allow None for kimi_api_key."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.kimi_api_key is None or isinstance(test_settings.kimi_api_key, str)