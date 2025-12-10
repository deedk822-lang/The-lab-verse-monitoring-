import os
from pydantic_settings import BaseSettings
from typing import Optional

# --- Start of Google Colab Integration ---
# Check if running in Google Colab environment
IN_COLAB = 'COLAB_GPU' in os.environ

colab_userdata = None
if IN_COLAB:
    try:
        from google.colab import userdata as colab_userdata
        print("Successfully imported Google Colab userdata.")
    except ImportError:
        print("Could not import Google Colab userdata. Skipping Colab-specific secret loading.")
        colab_userdata = None
# --- End of Google Colab Integration ---

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

# --- Load secrets from Google Colab if available ---
if colab_userdata:
    print("Attempting to load secrets from Google Colab userdata...")
    for field_name in Settings.model_fields:
        # Check if the field is not already set from .env or environment
        if getattr(settings, field_name) is None:
            try:
                # Attempt to get the secret from Colab userdata
                secret_value = colab_userdata.get(field_name)
                if secret_value:
                    setattr(settings, field_name, secret_value)
                    print(f"Loaded secret for '{field_name}' from Colab userdata.")
            except Exception as e:
                # This might happen if the key doesn't exist. It's safe to ignore.
                pass
    print("Finished loading secrets from Google Colab userdata.")
# --- End of secret loading ---
