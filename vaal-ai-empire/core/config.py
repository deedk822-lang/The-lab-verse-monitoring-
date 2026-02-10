
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI Models
    COHERE_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    HUGGINGFACE_TOKEN: str | None = None

    # Social Media
    AYRSHARE_API_KEY: str | None = None
    SOCIALPILOT_API_KEY: str | None = None
    TWITTER_BEARER_TOKEN: str | None = None

    # MailChimp
    MAILCHIMP_API_KEY: str | None = None
    MAILCHIMP_SERVER_PREFIX: str = "us10"

    # Asana
    ASANA_ACCESS_TOKEN: str | None = None
    ASANA_WORKSPACE_GID: str | None = None

    # Jira
    JIRA_API_TOKEN: str | None = None
    JIRA_EMAIL: str | None = None
    JIRA_BASE_URL: str | None = None

    # Application
    APP_NAME: str = "Vaal AI Empire"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
