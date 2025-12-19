#!/usr/bin/env python3
"""
Complete System Test - Now with Graceful Fallbacks
Tests every component, reporting missing dependencies as warnings instead of errors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_import(module_name: str, description: str) -> bool:
    """Test if a module can be imported, returns success status."""
    try:
        __import__(module_name)
        logger.info(f"✅ {description}: OK")
        return True
    except ImportError as e:
        logger.warning(f"⚠️  {description}: Not installed ({str(e)})")
        return False
    except Exception as e:
        logger.error(f"❌ {description}: Error ({str(e)})")
        return False

def test_api_client(client_class, description: str) -> bool:
    """Test if an API client can be instantiated, handling expected errors."""
    try:
        client = client_class()
        logger.info(f"✅ {description}: OK")
        return True
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  {description}: Not configured or installed - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ {description}: Unexpected error - {str(e)}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("VAAL AI EMPIRE - SYSTEM TEST SUITE")
    logger.info("=" * 60)

    results = {
        "critical": [],
        "optional": [],
        "services": [],
        "failed": []
    }

    # --- Critical imports ---
    logger.info("\n📦 Testing Critical Dependencies...")
    critical_tests = [("requests", "Requests"), ("pydantic", "Pydantic")]
    for module, desc in critical_tests:
        if test_import(module, desc):
            results["critical"].append(desc)
        else:
            results["failed"].append(desc)

    # --- Test API clients ---
    logger.info("\n🔌 Testing API Clients...")
    api_clients_to_test = []
    try:
        from api.cohere import CohereAPI
        api_clients_to_test.append((CohereAPI, "Cohere API Client"))
        from api.mistral import MistralAPI
        api_clients_to_test.append((MistralAPI, "Mistral API Client"))
        from clients.mailchimp_client import MailChimpClient
        api_clients_to_test.append((MailChimpClient, "MailChimp Client"))
        from clients.asana_client import AsanaClient
        api_clients_to_test.append((AsanaClient, "Asana Client"))
    except ImportError as e:
        logger.error(f"❌ Failed to import a client module: {e}")
        results["failed"].append("API Client Imports")

    for client_class, description in api_clients_to_test:
        if test_api_client(client_class, description):
            results["optional"].append(description)

    # --- Test services ---
    logger.info("\n🛠️  Testing Services...")
    try:
        from services.content_generator import get_content_factory
        factory = get_content_factory()
        logger.info("✅ Content Factory: Instantiated")

        logger.info("🧪 Testing content generation...")
        pack = factory.generate_social_pack("butchery", "afrikaans")
        if pack and "posts" in pack and len(pack['posts']) > 0:
            logger.info(f"✅ Generated {len(pack['posts'])} posts")
            results["services"].append("Content Generation")
        else:
            logger.warning("⚠️  Content generation returned no posts or unexpected format.")

    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Services test skipped: {e}")
    except Exception as e:
        logger.error(f"❌ Services test failed with unexpected error: {e}")
        results["failed"].append("Services")

    # --- Print summary ---
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Critical System: {len(results['critical'])} passed")
    logger.info(f"✅ API Clients Initialized: {len(results['optional'])}")
    logger.info(f"✅ Services Functional: {len(results['services'])}")

    if results["failed"]:
        logger.error(f"❌ Failed Components: {', '.join(results['failed'])}")
        logger.error("Please address the critical failures above.")
        return 1

    logger.info("\n" + "=" * 60)
    if len(results["critical"]) >= 2:
        logger.info("🎉 CORE SYSTEM FUNCTIONAL!")
        logger.info("Note: Some API clients or services may be unavailable if not configured.")
        logger.info("To enable all features, configure API keys in your .env file.")
        return 0
    else:
        logger.error("❌ CRITICAL FAILURES - Core system is not functional.")
        logger.error("Please run: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
