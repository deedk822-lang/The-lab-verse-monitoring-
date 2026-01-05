#!/usr/bin/env python3
"""
validate_env.py - Production Environment Validator
Version: 2.0.0

Validates all required API keys, paths, and dependencies.
Creates proper .env.template for team members.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_info(msg: str):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def print_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def print_step(msg: str):
    print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")

class EnvironmentValidator:
    def __init__(self):
        self.repo_root = self._get_repo_root()
        self.env_file = self.repo_root / ".env"
        self.env_template = self.repo_root / ".env.template"
        self.validation_report = {
            "required_keys": {},
            "optional_keys": {},
            "paths": {},
            "dependencies": {},
            "overall_status": "pending"
        }

        # Required API keys for production
        self.required_keys = {
            "KIMI_API_KEY": "Moonshot AI (Kimi) - Primary reasoning engine",
            "MISTRAL_API_KEY": "Mistral AI - Secondary model for validation",
            "GROQ_API_KEY": "Groq - Fast inference for real-time tasks",
            "HUGGINGFACE_API_KEY": "HuggingFace - Model downloads and inference"
        }

        # Optional but recommended
        self.optional_keys = {
            "GITHUB_TOKEN": "GitHub API - For PR creation and repo management",
            "SLACK_WEBHOOK_URL": "Slack - For notifications and alerts",
            "PROMETHEUS_URL": "Prometheus - Metrics collection",
            "GRAFANA_API_KEY": "Grafana - Dashboard management",
            "SENTRY_DSN": "Sentry - Error tracking"
        }

        # Required paths
        self.required_paths = [
            ".jules",
            ".jules/logs",
            ".jules/temp",
            ".jules/validation-results",
            "agents",
            "clients",
            "tools",
            "scoring",
            "governance",
            "scripts"
        ]

        # Required dependencies
        self.python_deps = [
            "langchain",
            "pydantic",
            "requests",
            "python-dotenv"
        ]

        self.node_deps = [
            "express",
            "axios",
            "dotenv"
        ]

    def _get_repo_root(self) -> Path:
        """Get repository root directory"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return Path.cwd()

    def validate_api_keys(self) -> bool:
        """Validate all required and optional API keys"""
        print_step("Validating API keys...")

        # Load .env if exists
        if self.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
        else:
            print_warn(f".env file not found at {self.env_file}")

        all_valid = True

        # Check required keys
        for key, description in self.required_keys.items():
            value = os.getenv(key)
            if value and len(value) > 10:  # Assume keys are at least 10 chars
                print_info(f"✓ {key}: Valid ({description})")
                self.validation_report["required_keys"][key] = {
                    "status": "valid",
                    "description": description
                }
            else:
                print_error(f"✗ {key}: Missing or invalid ({description})")
                self.validation_report["required_keys"][key] = {
                    "status": "missing",
                    "description": description
                }
                all_valid = False

        # Check optional keys
        for key, description in self.optional_keys.items():
            value = os.getenv(key)
            if value and len(value) > 5:
                print_info(f"✓ {key}: Valid ({description})")
                self.validation_report["optional_keys"][key] = {
                    "status": "valid",
                    "description": description
                }
            else:
                print_warn(f"⚠ {key}: Not set ({description})")
                self.validation_report["optional_keys"][key] = {
                    "status": "not_set",
                    "description": description
                }

        return all_valid

    def validate_paths(self) -> bool:
        """Validate and create required directory structure"""
        print_step("Validating directory structure...")

        all_valid = True
        for path_str in self.required_paths:
            path = self.repo_root / path_str
            if path.exists():
                print_info(f"✓ Directory exists: {path_str}")
                self.validation_report["paths"][path_str] = "exists"
            else:
                print_warn(f"⚠ Creating directory: {path_str}")
                path.mkdir(parents=True, exist_ok=True)
                self.validation_report["paths"][path_str] = "created"

        # Verify critical files
        critical_files = {
            "requirements.txt": "Python dependencies",
            "package.json": "Node.js dependencies (if applicable)",
            ".semgrep/rules.yml": "Security scanning rules"
        }

        for file_name, description in critical_files.items():
            file_path = self.repo_root / file_name
            if file_path.exists():
                print_info(f"✓ File exists: {file_name} ({description})")
            else:
                print_warn(f"⚠ Missing: {file_name} ({description})")
                if not file_name.startswith('.'):
                    all_valid = False

        return all_valid

    def validate_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print_step("Validating dependencies...")

        all_valid = True

        # Check Python dependencies
        print_info("Checking Python dependencies...")
        for dep in self.python_deps:
            try:
                __import__(dep.replace("-", "_"))
                print_info(f"✓ Python: {dep} installed")
                self.validation_report["dependencies"][f"python:{dep}"] = "installed"
            except ImportError:
                print_error(f"✗ Python: {dep} NOT installed")
                self.validation_report["dependencies"][f"python:{dep}"] = "missing"
                all_valid = False

        # Check Node.js dependencies (if package.json exists)
        package_json = self.repo_root / "package.json"
        if package_json.exists():
            print_info("Checking Node.js dependencies...")
            node_modules = self.repo_root / "node_modules"
            if node_modules.exists():
                for dep in self.node_deps:
                    dep_path = node_modules / dep
                    if dep_path.exists():
                        print_info(f"✓ Node.js: {dep} installed")
                        self.validation_report["dependencies"][f"node:{dep}"] = "installed"
                    else:
                        print_error(f"✗ Node.js: {dep} NOT installed")
                        self.validation_report["dependencies"][f"node:{dep}"] = "missing"
                        all_valid = False
            else:
                print_warn("⚠ node_modules not found - run: npm install")
                all_valid = False

        return all_valid

    def create_env_template(self):
        """Create .env.template with all required variables"""
        print_step("Creating .env.template...")

        template_content = """# ============================================================
# Autonomous Builder Platform - Environment Configuration
# ============================================================
# Copy this file to .env and fill in your actual API keys
# Generated: {timestamp}

# ============================================================
# REQUIRED API KEYS
# ============================================================

# Moonshot AI (Kimi) - Primary reasoning engine
# Get your key from: https://platform.moonshot.cn
KIMI_API_KEY=your_kimi_api_key_here

# Mistral AI - Secondary model for validation
# Get your key from: https://console.mistral.ai
MISTRAL_API_KEY=your_mistral_api_key_here

# Groq - Fast inference for real-time tasks
# Get your key from: https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# HuggingFace - Model downloads and inference
# Get your key from: https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY=your_huggingface_token_here

# ============================================================
# OPTIONAL INTEGRATIONS
# ============================================================

# GitHub API - For PR creation and repo management
# GITHUB_TOKEN=your_github_token_here

# Slack - For notifications and alerts
# SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# Prometheus - Metrics collection
# PROMETHEUS_URL=http://localhost:9090

# Grafana - Dashboard management
# GRAFANA_API_KEY=your_grafana_api_key_here

# Sentry - Error tracking
# SENTRY_DSN=your_sentry_dsn_here

# ============================================================
# SYSTEM CONFIGURATION
# ============================================================

# Repository root (auto-detected if not set)
REPO_ROOT={repo_root}

# Environment (development, staging, production)
ENVIRONMENT=production

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable autonomous deployment (true/false)
AUTO_DEPLOY_ENABLED=true

# Confidence threshold for auto-merge (0-100)
AUTO_MERGE_THRESHOLD=95

# Maximum files for auto-merge
MAX_FILES_AUTO_MERGE=10

# ============================================================
# SECURITY
# ============================================================

# Enable Semgrep security scanning
SEMGREP_ENABLED=true

# Protected paths (comma-separated patterns)
PROTECTED_PATHS=.github/workflows,config,**/auth/**,**/payment/**

# ============================================================
# MONITORING
# ============================================================

# Grafana Dashboard URL
GRAFANA_URL=http://localhost:3000

# Prometheus Metrics Port
PROMETHEUS_PORT=9090

# Health check interval (seconds)
HEALTH_CHECK_INTERVAL=60
""".format(
            timestamp=subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            repo_root=self.repo_root
        )

        self.env_template.write_text(template_content)
        print_info(f"✓ Created {self.env_template}")

        # If .env doesn't exist, create it from template
        if not self.env_file.exists():
            self.env_file.write_text(template_content)
            print_warn(f"⚠ Created {self.env_file} - PLEASE UPDATE WITH YOUR ACTUAL API KEYS")

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        print_step("Generating validation report...")

        # Determine overall status
        required_keys_valid = all(
            v["status"] == "valid"
            for v in self.validation_report["required_keys"].values()
        )

        deps_valid = all(
            v == "installed"
            for k, v in self.validation_report["dependencies"].items()
        )

        if required_keys_valid and deps_valid:
            self.validation_report["overall_status"] = "ready"
            print_info("✓ System is READY for production")
        elif required_keys_valid:
            self.validation_report["overall_status"] = "needs_dependencies"
            print_warn("⚠ API keys valid but dependencies need installation")
        else:
            self.validation_report["overall_status"] = "needs_configuration"
            print_error("✗ System needs configuration before use")

        # Save report
        report_file = self.repo_root / ".jules" / "validation-report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(self.validation_report, indent=2))
        print_info(f"✓ Report saved to {report_file}")

        return self.validation_report

    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        # Required keys
        print(f"\n{Colors.BLUE}Required API Keys:{Colors.NC}")
        for key, info in self.validation_report["required_keys"].items():
            status = "✓" if info["status"] == "valid" else "✗"
            color = Colors.GREEN if info["status"] == "valid" else Colors.RED
            print(f"  {color}{status}{Colors.NC} {key}: {info['description']}")

        # Optional keys
        print(f"\n{Colors.BLUE}Optional Keys:{Colors.NC}")
        for key, info in self.validation_report["optional_keys"].items():
            status = "✓" if info["status"] == "valid" else "⚠"
            color = Colors.GREEN if info["status"] == "valid" else Colors.YELLOW
            print(f"  {color}{status}{Colors.NC} {key}: {info['description']}")

        # Dependencies
        missing_deps = [
            dep for dep, status in self.validation_report["dependencies"].items()
            if status == "missing"
        ]

        if missing_deps:
            print(f"\n{Colors.YELLOW}Missing Dependencies:{Colors.NC}")
            for dep in missing_deps:
                print(f"  ✗ {dep}")

            if any("python:" in dep for dep in missing_deps):
                print(f"\n{Colors.BLUE}Install Python dependencies:{Colors.NC}")
                print("  pip install -r requirements.txt")

            if any("node:" in dep for dep in missing_deps):
                print(f"\n{Colors.BLUE}Install Node.js dependencies:{Colors.NC}")
                print("  npm install")

        # Overall status
        status = self.validation_report["overall_status"]
        print(f"\n{Colors.BLUE}Overall Status:{Colors.NC} ", end="")
        if status == "ready":
            print(f"{Colors.GREEN}✓ READY FOR PRODUCTION{Colors.NC}")
            print(f"\nNext step: Run production_startup.sh")
        elif status == "needs_dependencies":
            print(f"{Colors.YELLOW}⚠ NEEDS DEPENDENCIES{Colors.NC}")
            print(f"\nInstall dependencies, then run this script again")
        else:
            print(f"{Colors.RED}✗ NEEDS CONFIGURATION{Colors.NC}")
            print(f"\nUpdate .env with your API keys, then run this script again")

        print("="*60 + "\n")

    def run(self) -> bool:
        """Run all validations"""
        print_info("="*60)
        print_info("  Environment Validation Tool v2.0")
        print_info("="*60)
        print_info(f"Repository: {self.repo_root}\n")

        # Run validations
        keys_valid = self.validate_api_keys()
        paths_valid = self.validate_paths()
        deps_valid = self.validate_dependencies()

        # Create template
        self.create_env_template()

        # Generate and save report
        self.generate_report()

        # Print summary
        self.print_summary()

        return self.validation_report["overall_status"] == "ready"


if __name__ == "__main__":
    validator = EnvironmentValidator()
    is_ready = validator.run()

    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)