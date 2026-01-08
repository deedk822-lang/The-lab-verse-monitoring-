#!/usr/bin/env python3
"""
scripts/load_github_secrets.py

Load secrets from GitHub repository for local development and CI/CD.
Provides unified secret access across all environments.

Usage:
    # In CI/CD (GitHub Actions) - secrets available as env vars
    from scripts.load_github_secrets import ensure_secrets_loaded
    ensure_secrets_loaded()

    # Locally - fetch from GitHub API or use .env
    load_secrets_from_github(token="ghp_...", repo="owner/repo")
"""

import os
import sys
import json
import logging
from typing import Dict, Optional, List
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_github_actions() -> bool:
    """Check if running in GitHub Actions."""
    return os.getenv('GITHUB_ACTIONS') == 'true'


def load_from_dotenv() -> bool:
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"✓ Loaded environment from {env_path}")
            return True
        else:
            logger.warning(f".env file not found at {env_path}")
            return False
    except ImportError:
        logger.warning("python-dotenv not installed. Run: pip install python-dotenv")
        return False


def fetch_github_secret_names(token: str, repo: str) -> List[str]:
    """
    Fetch list of secret names from GitHub repository.

    Args:
        token: GitHub personal access token with repo scope
        repo: Repository in format "owner/repo"

    Returns:
        List of secret names
    """
    url = f"https://api.github.com/repos/{repo}/actions/secrets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        secret_names = [secret['name'] for secret in data.get('secrets', [])]
        logger.info(f"✓ Found {len(secret_names)} secrets in GitHub")
        return secret_names

    except requests.exceptions.RequestException as e:
        logger.exception("Failed to fetch secrets from GitHub")
        return []


def map_secret_to_env_var(secret_name: str) -> str:
    """
    Map GitHub secret name to environment variable name.
    Most are 1:1, but handle special cases.
    """
    # Special mappings
    mappings = {
        'PERSONAL_ACCESS_TOKEN': 'GITHUB_TOKEN',
        'PERSONAL_TOKEN': 'GITHUB_TOKEN',
        'KAGGEL_API_KEY': 'KAGGLE_API_KEY',  # Fix typo
        'ARYSHARE_API_KEY': 'AYRSHARE_API_KEY',  # Fix typo
    }

    return mappings.get(secret_name, secret_name)


# ============================================
# REQUIRED SECRETS MAPPING
# ============================================
# Map secret categories to GitHub secret names

REQUIRED_SECRETS = {
    'core': [
        'GITHUB_TOKEN',  # PERSONAL_ACCESS_TOKEN or PERSONAL_TOKEN
    ],

    'ai_providers': [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'GROQ_API_KEY',
        'HUGGINGFACE_API_KEY',  # or HF_API_TOKEN
        'COHERE_API_KEY',
        'PERPLEXITY_API_KEY',
        'MISTRAL_API_KEY',
        'GEMINI_API_KEY',
    ],

    'monitoring': [
        'GRAFANA_API_KEY',
        'DATADOG_API_KEY',
    ],

    'project_management': [
        'JIRA_USER_EMAIL',
        'JIRA_LINK',
        'ASANA_INTEGRATIONS_ACTIONS',
        'HUBSPOT_API_KEY',
        'NOTION_API_KEY',
    ],

    'payment': [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
    ],

    'communication': [
        'MAILCHIMP_API_KEY',
        'WHATSAPP_PHONE_ID',
    ],

    'cloud': [
        'ACCESS_KEY_ID',  # AWS
        'ACCESS_KEY_SECRET',  # AWS
        'VERCEL_TOKEN',
        'FLYIO_API_KEY',
    ],

    'security': [
        'JWT_SECRET',
        'SESSION_SECRET',
    ],
}


def get_all_required_secrets() -> List[str]:
    """Get flattened list of all required secrets."""
    secrets = []
    for category in REQUIRED_SECRETS.values():
        secrets.extend(category)
    return secrets


def ensure_secrets_loaded() -> Dict[str, str]:
    """
    Ensure secrets are loaded from appropriate source.

    Priority:
    1. GitHub Actions environment (CI/CD)
    2. Local .env file (development)
    3. Environment variables (already set)

    Returns:
        Dict of loaded secrets and their sources
    """
    loaded = {}

    if is_github_actions():
        logger.info("Running in GitHub Actions - using CI environment")
        source = "github_actions"

        # In GitHub Actions, secrets are already in environment
        for secret_name in get_all_required_secrets():
            value = os.getenv(secret_name)
            if value:
                loaded[secret_name] = source
                logger.debug(f"✓ {secret_name} loaded from {source}")

    else:
        logger.info("Running locally - loading from .env")
        load_from_dotenv()
        source = "dotenv"

        for secret_name in get_all_required_secrets():
            value = os.getenv(secret_name)
            if value:
                loaded[secret_name] = source
                logger.debug(f"✓ {secret_name} loaded from {source}")

    logger.info(f"✓ Loaded {len(loaded)} secrets from {source}")
    return loaded


def validate_required_secrets(categories: List[str] = None) -> bool:
    """
    Validate that required secrets are present.

    Args:
        categories: List of categories to check. If None, checks all.

    Returns:
        True if all required secrets in specified categories are present
    """
    if categories is None:
        categories = list(REQUIRED_SECRETS.keys())

    missing = []

    for category in categories:
        if category not in REQUIRED_SECRETS:
            logger.warning(f"Unknown category: {category}")
            continue

        for secret_name in REQUIRED_SECRETS[category]:
            if not os.getenv(secret_name):
                missing.append((category, secret_name))

    if missing:
        logger.error(f"Missing {len(missing)} required secrets:")
        for category, secret in missing:
            logger.error(f"  [{category}] {secret}")
        return False

    logger.info(f"✓ All required secrets validated for categories: {', '.join(categories)}")
    return True


def get_secret(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get a secret from environment with optional default.

    Args:
        key: Secret name
        default: Default value if not found
        required: If True, raises error if not found

    Returns:
        Secret value or default
    """
    value = os.getenv(key, default)

    if value is None:
        if required:
            raise ValueError(f"Required secret '{key}' not found in environment")
        logger.warning(f"Secret '{key}' not found in environment")

    return value


def create_env_file_from_github(
    token: str,
    repo: str,
    output_path: str = ".env.template"
) -> bool:
    """
    Create .env template file from GitHub secrets.

    Args:
        token: GitHub personal access token
        repo: Repository in format "owner/repo"
        output_path: Path to output file

    Returns:
        True if successful
    """
    logger.info(f"Fetching secrets from GitHub repo: {repo}")
    secret_names = fetch_github_secret_names(token, repo)

    if not secret_names:
        logger.error("No secrets found or failed to fetch")
        return False

    # Group secrets by category
    categorized = {cat: [] for cat in REQUIRED_SECRETS.keys()}
    categorized['other'] = []

    for secret_name in sorted(secret_names):
        env_var = map_secret_to_env_var(secret_name)

        # Find category
        found_category = False
        for category, secrets in REQUIRED_SECRETS.items():
            if env_var in secrets:
                categorized[category].append((secret_name, env_var))
                found_category = True
                break

        if not found_category:
            categorized['other'].append((secret_name, env_var))

    # Write .env template
    with open(output_path, 'w') as f:
        f.write("# ============================================\n")
        f.write("# The Lab-Verse Monitoring - Environment Configuration\n")
        f.write("# ============================================\n")
        f.write("# Generated from GitHub Secrets\n")
        f.write(f"# Total secrets: {len(secret_names)}\n")
        f.write("# \n")
        f.write("# INSTRUCTIONS:\n")
        f.write("# 1. Copy this file to .env\n")
        f.write("# 2. Fill in the values from GitHub Secrets\n")
        f.write("# 3. NEVER commit .env to git\n")
        f.write("# ============================================\n\n")

        # Write each category
        category_names = {
            'core': 'CORE CREDENTIALS',
            'ai_providers': 'AI PROVIDERS',
            'monitoring': 'MONITORING & ANALYTICS',
            'project_management': 'PROJECT MANAGEMENT',
            'payment': 'PAYMENT PROCESSING',
            'communication': 'COMMUNICATION',
            'cloud': 'CLOUD PROVIDERS',
            'security': 'SECURITY KEYS',
            'other': 'OTHER SECRETS'
        }

        for category, display_name in category_names.items():
            if not categorized[category]:
                continue

            f.write(f"# ============================================\n")
            f.write(f"# {display_name}\n")
            f.write(f"# ============================================\n")

            for github_name, env_var in categorized[category]:
                if github_name != env_var:
                    f.write(f"# GitHub Secret: {github_name}\n")
                f.write(f"{env_var}=your_{env_var.lower()}_here\n")

            f.write("\n")

    logger.info(f"✓ Created {output_path} with {len(secret_names)} secrets")
    logger.info(f"  Run: cp {output_path} .env")
    return True


# ============================================
# AUTO-LOAD ON IMPORT
# ============================================
if __name__ != "__main__":
    try:
        ensure_secrets_loaded()
    except Exception as e:
        logger.error(f"Failed to auto-load secrets: {e}")


# ============================================
# CLI INTERFACE
# ============================================
def main():
    """CLI interface for secret management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub Secrets Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--validate",
        nargs='*',
        metavar='CATEGORY',
        help="Validate secrets for categories (all if not specified)"
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Show loaded secrets (values masked)"
    )

    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create .env template from GitHub secrets"
    )

    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )

    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY"),
        help="GitHub repository (e.g., 'owner/repo'). Required for local runs if GITHUB_REPOSITORY is not set."
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create template from GitHub
    if args.create_template:
        token = args.token or os.getenv('GITHUB_TOKEN')
        if not token:
            print("❌ GitHub token required. Use --token or set GITHUB_TOKEN")
            sys.exit(1)

        if not args.repo:
            print("❌ GitHub repository required. Use --repo or set GITHUB_REPOSITORY")
            sys.exit(1)

        if create_env_file_from_github(token, args.repo):
            print(f"\n✓ Created .env.template")
            print("  Next steps:")
            print("  1. cp .env.template .env")
            print("  2. Fill in the secret values")
            sys.exit(0)
        else:
            print("❌ Failed to create template")
            sys.exit(1)

    # Load secrets
    loaded = ensure_secrets_loaded()

    # Show loaded secrets
    if args.show:
        print("\n" + "="*70)
        print("LOADED SECRETS")
        print("="*70)

        # Group by category
        for category, secrets in REQUIRED_SECRETS.items():
            found_in_category = False
            for secret in secrets:
                if secret in loaded:
                    if not found_in_category:
                        print(f"\n[{category.upper().replace('_', ' ')}]")
                        found_in_category = True

                    value = os.getenv(secret, "")
                    masked = value[:8] + "..." if len(value) > 8 else "***"
                    print(f"  ✓ {secret:35s} {masked}")

        print("\n" + "="*70)
        print(f"Total: {len(loaded)} secrets loaded")
        print("="*70 + "\n")

    # Validate
    if args.validate is not None:
        categories = args.validate if args.validate else None
        if validate_required_secrets(categories):
            print("✓ All required secrets validated")
            sys.exit(0)
        else:
            print("✗ Validation failed")
            sys.exit(1)

    print(f"\n✓ Loaded {len(loaded)} secrets successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()