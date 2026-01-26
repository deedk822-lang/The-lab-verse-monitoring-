from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI Models
    COHERE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None

    # Social Media
    AYRSHARE_API_KEY: Optional[str] = None
    SOCIALPILOT_API_KEY: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None

    # MailChimp
    MAILCHIMP_API_KEY: Optional[str] = None
    MAILCHIMP_SERVER_PREFIX: str = "us10"

    # Asana
    ASANA_ACCESS_TOKEN: Optional[str] = None
    ASANA_WORKSPACE_GID: Optional[str] = None

    # Jira
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_BASE_URL: Optional[str] = None

    # Application
    APP_NAME: str = "Vaal AI Empire"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
