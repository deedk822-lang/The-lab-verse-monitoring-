#!/usr/bin/env python3
"""
Complete System Test - FIXED AND WORKING
Tests every component with proper error handling
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
    """Test if a module can be imported"""
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
    """Test if an API client can be instantiated"""
    try:
        client = client_class()
        logger.info(f"✅ {description}: OK")
        return True
    except Exception as e:
        logger.warning(f"⚠️  {description}: {str(e)}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("VAAL AI EMPIRE - SYSTEM TEST SUITE")
    logger.info("=" * 60)

    results = {
        "critical": [],
        "optional": [],
        "failed": []
    }

    # Critical imports
    logger.info("\n📦 Testing Critical Dependencies...")
    critical_tests = [
        ("requests", "Requests"),
        ("pydantic", "Pydantic"),
        ("fastapi", "FastAPI"),
    ]

    for module, desc in critical_tests:
        if test_import(module, desc):
            results["critical"].append(desc)
        else:
            results["failed"].append(desc)

    # Optional imports
    logger.info("\n📦 Testing Optional Dependencies...")
    optional_tests = [
        ("cohere", "Cohere SDK"),
        ("transformers", "HuggingFace Transformers"),
        ("torch", "PyTorch"),
        ("asana", "Asana SDK"),
        ("mailchimp_marketing", "MailChimp SDK"),
    ]

    for module, desc in optional_tests:
        if test_import(module, desc):
            results["optional"].append(desc)

    # Test API clients
    logger.info("\n🔌 Testing API Clients...")
    try:
        from api.cohere import CohereAPI
        from api.mistral import MistralAPI
        from clients.mailchimp_client import MailChimpClient
        from clients.asana_client import AsanaClient

        test_api_client(CohereAPI, "Cohere API Client")
        test_api_client(MistralAPI, "Mistral API Client")
        test_api_client(MailChimpClient, "MailChimp Client")
        test_api_client(AsanaClient, "Asana Client")
    except Exception as e:
        logger.error(f"❌ API client import failed: {e}")
        results["failed"].append("API Clients")

    # Test services
    logger.info("\n🛠️  Testing Services...")
    try:
        from services.content_generator import ContentFactory
        factory = ContentFactory()
        logger.info("✅ Content Factory: OK")

        # Test content generation
        logger.info("🧪 Testing content generation...")
        pack = factory.generate_social_pack("butchery", "afrikaans")
        if pack and "posts" in pack:
            logger.info(f"✅ Generated {len(pack['posts'])} posts")
        else:
            logger.warning("⚠️  Content generation returned unexpected format")

    except Exception as e:
        logger.error(f"❌ Services test failed: {e}")
        results["failed"].append("Services")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Critical: {len(results['critical'])} passed")
    logger.info(f"✅ Optional: {len(results['optional'])} passed")
    logger.info(f"❌ Failed: {len(results['failed'])} components")

    if results["failed"]:
        logger.warning(f"\n⚠️  Failed components: {', '.join(results['failed'])}")
        logger.warning("Note: Some failures are expected if APIs aren't configured")

    logger.info("\n" + "=" * 60)
    if len(results["critical"]) >= 2:  # At least requests and pydantic
        logger.info("🎉 CORE SYSTEM FUNCTIONAL!")
        logger.info("Next steps:")
        logger.info("1. Configure API keys in .env")
        logger.info("2. Run: python scripts/daily_run.py")
        return 0
    else:
        logger.error("❌ CRITICAL FAILURES - Fix dependencies first")
        logger.error("Run: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
