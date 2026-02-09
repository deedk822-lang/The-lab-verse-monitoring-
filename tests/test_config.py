import os

from server.config import get_settings


def test_settings_can_load():
    os.environ["JWT_SECRET"] = "tmp"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["OIDC_DISCOVERY"] = "https://demo.com/.well-known/openid-configuration"

    get_settings.cache_clear()
    settings = get_settings()
    assert settings.jwt_secret == "tmp"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.oidc_discovery == "https://demo.com/.well-known/openid-configuration"
