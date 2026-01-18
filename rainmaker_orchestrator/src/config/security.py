"""Security configuration module with strict type safety."""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SecurityConfig:
    """Typed security configuration with environment isolation."""
    aliyun_access_key_id: str
    aliyun_access_key_secret: str
    aliyun_region: str = "cn-shanghai"
    ecs_instance_id: Optional[str] = None
    ecs_host: Optional[str] = None
    ecs_user: str = "root"
    workspace_path: str = "/app/workspace"
    log_level: str = "INFO"
    environment: str = "production"
    zai_api_key: Optional[str] = None
    ifcloud_api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    session_secret: Optional[str] = None

def get_security_config() -> SecurityConfig:
    """Load security configuration with strict validation."""
    # Validate required environment variables
    required_vars = [
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
        "ZAI_API_KEY",
        "IFCLOUD_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return SecurityConfig(
        aliyun_access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID", ""),
        aliyun_access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET", ""),
        aliyun_region=os.getenv("ALIYUN_REGION", "cn-shanghai"),
        ecs_instance_id=os.getenv("ECS_INSTANCE_ID"),
        ecs_host=os.getenv("ECS_HOST"),
        ecs_user=os.getenv("ECS_USER", "root"),
        workspace_path=os.getenv("WORKSPACE_PATH", "/app/workspace"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "production"),
        zai_api_key=os.getenv("ZAI_API_KEY"),
        ifcloud_api_key=os.getenv("IFCLOUD_API_KEY"),
        jwt_secret=os.getenv("JWT_SECRET"),
        session_secret=os.getenv("SESSION_SECRET")
    )

def sanitize_input(input_str: Optional[str]) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not input_str:
        return ""
    # Remove potentially dangerous characters
    return input_str.replace("<", "").replace(">", "").replace('"', "").replace("'", "")

def redact_sensitive_info(obj: Any) -> Any:
    """Redact sensitive information from objects for logging."""
    if not obj or not isinstance(obj, (dict, list)):
        return obj

    sensitive_keywords = {
        "password", "secret", "token", "key", "credential",
        "accesskey", "secretkey", "apikey", "privatekey"
    }

    if isinstance(obj, list):
        return [redact_sensitive_info(item) for item in obj]

    result = {}
    for key, value in obj.items():
        lower_key = key.lower()
        if any(keyword in lower_key for keyword in sensitive_keywords):
            result[key] = "[REDACTED]"
        elif isinstance(value, (dict, list)):
            result[key] = redact_sensitive_info(value)
        else:
            result[key] = value

    return result
