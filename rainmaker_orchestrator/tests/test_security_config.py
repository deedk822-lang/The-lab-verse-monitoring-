"""
Unit tests for security configuration management.
"""
import pytest
import os
from unittest.mock import patch
from rainmaker_orchestrator.src.config.security import get_security_config, SecurityConfig

class TestSecurityConfig:
    """Test suite for SecurityConfig dataclass and get_security_config function."""

    def test_get_security_config_with_all_env_vars(self):
        """Should load all settings from environment variables."""
        env_vars = {
            'ALIYUN_ACCESS_KEY_ID': 'test_id',
            'ALIYUN_ACCESS_KEY_SECRET': 'test_secret',
            'ZAI_API_KEY': 'zai_key',
            'IFCLOUD_API_KEY': 'ifcloud_key',
            'ECS_INSTANCE_ID': 'ecs_instance',
            'ECS_HOST': 'ecs_host',
            'ECS_USER': 'ecs_user',
            'WORKSPACE_PATH': '/test/workspace',
            'JWT_SECRET': 'jwt_secret',
            'SESSION_SECRET': 'session_secret'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = get_security_config()

            assert config.aliyun_access_key_id == 'test_id'
            assert config.aliyun_access_key_secret == 'test_secret'
            assert config.zai_api_key == 'zai_key'
            assert config.ifcloud_api_key == 'ifcloud_key'
            assert config.ecs_instance_id == 'ecs_instance'
            assert config.ecs_host == 'ecs_host'
            assert config.ecs_user == 'ecs_user'
            assert config.workspace_path == '/test/workspace'
            assert config.jwt_secret == 'jwt_secret'
            assert config.session_secret == 'session_secret'

    def test_get_security_config_with_missing_required_vars(self):
        """Should raise ValueError if required environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_security_config()

    def test_get_security_config_with_defaults(self):
        """Should use default values for optional fields when not provided."""
        env_vars = {
            'ALIYUN_ACCESS_KEY_ID': 'test_id',
            'ALIYUN_ACCESS_KEY_SECRET': 'test_secret',
            'ZAI_API_KEY': 'zai_key',
            'IFCLOUD_API_KEY': 'ifcloud_key',
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_security_config()

            assert config.aliyun_region == 'cn-shanghai'
            assert config.ecs_user == 'root'
            assert config.workspace_path == '/app/workspace'
            assert config.ecs_instance_id is None
            assert config.ecs_host is None
            assert config.jwt_secret is None
            assert config.session_secret is None
