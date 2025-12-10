#!/bin/bash
set -e

echo "⚙️ UPGRADING CONFIGURATION ENGINE..."
echo "   - Standard: Pydantic BaseSettings"
echo "   - Compatibility: Google Colab + Server + Local"

# 1. INSTALL PYDANTIC SETTINGS
pip install pydantic-settings --upgrade --quiet

# 2. REWRITE CONFIG CORE (src/core/config.py)
# This replaces the old simple class with the robust Pydantic model
# that automatically detects if it's in Colab or a Server.

cat << 'EOF' > vaal-ai-empire/src/core/config.py
import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConfigEngine")

# --- GOOGLE COLAB INTEGRATION ---
IN_COLAB = 'COLAB_GPU' in os.environ
colab_userdata = None

if IN_COLAB:
    try:
        from google.colab import userdata as colab_userdata
        logger.info("✅ Detected Google Colab Environment.")
    except ImportError:
        logger.warning("⚠️ In Colab but failed to import userdata.")

class Settings(BaseSettings):
    # ALIBABA CORE
    DASHSCOPE_API_KEY: Optional[str] = None
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    OSS_ENDPOINT: str = "https://oss-eu-west-1.aliyuncs.com"
    OSS_BUCKET: str = "vaal-vault"

    # DEPARTMENT KEYS
    MISTRAL_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # EXTERNAL TOOLS
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_USER_EMAIL: Optional[str] = None
    NOTION_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiate Settings
settings = Settings()

# --- DYNAMIC SECRET LOADING (Colab Overlay) ---
if colab_userdata:
    logger.info("🔄 Syncing Colab Secrets...")
    for field in Settings.model_fields:
        # If config is missing in ENV, try finding it in Colab Secrets
        if getattr(settings, field) is None:
            try:
                secret_value = colab_userdata.get(field)
                if secret_value:
                    setattr(settings, field, secret_value)
                    logger.info(f"   > Loaded '{field}' from Colab.")
            except Exception:
                pass # Secret not defined in Colab, ignore.

# Global Access Point
config = settings
EOF

# 3. CREATE THE TEST SUITE
# This verifies the logic actually works as described in your review.
mkdir -p vaal-ai-empire/tests

cat << 'EOF' > vaal-ai-empire/tests/test_config_colab.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import importlib

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestConfig(unittest.TestCase):

    def _reload_config(self):
        """Force reload the config module to apply mocked env."""
        if 'src.core.config' in sys.modules:
            del sys.modules['src.core.config']
        return importlib.import_module('src.core.config')

    @patch.dict(os.environ, {'COLAB_GPU': '1'}, clear=True)
    def test_colab_loading(self):
        """Test: If in Colab, load secrets from userdata."""
        mock_userdata = MagicMock()
        mock_userdata.get.side_effect = lambda k: 'secret_123' if k == 'COHERE_API_KEY' else None

        with patch.dict('sys.modules', {'google.colab': MagicMock(userdata=mock_userdata)}):
            mod = self._reload_config()
            self.assertEqual(mod.settings.COHERE_API_KEY, 'secret_123')
            print("\n✅ Test Passed: Colab Secret Loaded")

    @patch.dict(os.environ, {}, clear=True)
    def test_server_loading(self):
        """Test: If NOT in Colab, ignore userdata."""
        with patch.dict('sys.modules', {'google.colab': MagicMock()}):
            mod = self._reload_config()
            self.assertIsNone(mod.settings.COHERE_API_KEY)
            print("✅ Test Passed: Server Mode (No Colab)")

if __name__ == '__main__':
    unittest.main()
EOF

echo "✅ CONFIGURATION ENGINE UPGRADED."
echo "   - Implementation: src/core/config.py"
echo "   - Tech: Pydantic Settings + Colab Userdata"
echo "   - Test: tests/test_config_colab.py"
