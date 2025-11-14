#!/usr/bin/env python3
"""
Security Artifact Generator using Moonshot AI
Generates missing security artifacts like trivy configs, secret rotation scripts, etc.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class SecurityArtifactGenerator:
    """Generate security artifacts using Moonshot AI"""
    
    ARTIFACT_TEMPLATES = {
        "trivy-scan": {
            "filename": ".github/workflows/trivy-scan.yml",
            "prompt": """Generate a GitHub Actions workflow for Trivy security scanning.

Requirements:
- Scan Docker images and filesystem
- Run on push to main and PRs
- Upload results to GitHub Security tab
- Fail on HIGH and CRITICAL vulnerabilities
- Support manual trigger
- Use latest Trivy version
- Scan multiple targets (Docker images, filesystem, IaC)

Return ONLY the YAML file content, no explanations."""
        },
        
        "secret-rotation": {
            "filename": "scripts/security/rotate-secrets.sh",
            "prompt": """Generate a bash script for rotating secrets and API keys.

Requirements:
- Support multiple secret types (API keys, passwords, tokens)
- Integration with common secret managers (AWS Secrets Manager, HashiCorp Vault)
- Backup old secrets before rotation
- Update environment files and configs
- Logging and audit trail
- Rollback capability
- Dry-run mode
- Error handling

Return ONLY the bash script content, no explanations."""
        },
        
        "k8s-security": {
            "filename": "k8s/security-policies.yaml",
            "prompt": """Generate Kubernetes security policies and manifests.

Requirements:
- Pod Security Policy / Pod Security Standards
- Network Policies for isolation
- RBAC configurations
- Security Context constraints
- Resource limits and quotas
- Image pull policies
- Service accounts with least privilege
- Secrets management

Return ONLY the Kubernetes YAML manifests, no explanations."""
        },
        
        "docker-security": {
            "filename": ".dockerignore",
            "prompt": """Generate a comprehensive .dockerignore file for security.

Requirements:
- Exclude sensitive files (.env, secrets, keys)
- Exclude development files
- Exclude version control
- Exclude build artifacts
- Exclude logs and temporary files
- Add comments explaining each section

Return ONLY the .dockerignore content, no explanations."""
        },
        
        "security-checklist": {
            "filename": "SECURITY_CHECKLIST.md",
            "prompt": """Generate a comprehensive security checklist for this repository.

Requirements:
- Code security (secrets, injection, validation)
- Infrastructure security (Docker, K8s, cloud)
- CI/CD security
- Dependency management
- Access control
- Monitoring and logging
- Incident response
- Compliance considerations
- Regular audit items

Format as a markdown checklist with checkboxes.

Return ONLY the markdown content, no explanations."""
        },
        
        "dependabot": {
            "filename": ".github/dependabot.yml",
            "prompt": """Generate a Dependabot configuration for automated dependency updates.

Requirements:
- Support for multiple package ecosystems (pip, npm, docker, github-actions)
- Weekly update schedule
- Group updates by type
- Auto-merge for patch updates
- Security updates prioritized
- Ignore specific dependencies if needed
- Commit message conventions

Return ONLY the YAML file content, no explanations."""
        },
        
        "pre-commit": {
            "filename": ".pre-commit-config.yaml",
            "prompt": """Generate a pre-commit configuration for security checks.

Requirements:
- Secret scanning (detect-secrets, gitleaks)
- Code quality (black, flake8, mypy for Python)
- Security linting (bandit, safety)
- YAML/JSON validation
- Trailing whitespace and EOF fixes
- Docker linting (hadolint)
- Shell script checking (shellcheck)

Return ONLY the YAML file content, no explanations."""
        },
        
        "security-policy": {
            "filename": "SECURITY.md",
            "prompt": """Generate a security policy document for this repository.

Requirements:
- Supported versions
- Reporting vulnerabilities (contact, process)
- Response timeline
- Disclosure policy
- Security best practices for contributors
- Bug bounty information (if applicable)

Return ONLY the markdown content, no explanations."""
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY environment variable not set")
        
        self.api_url = "https://api.moonshot.ai/v1/chat/completions"
        self.model = "moonshot-v1-8k"
    
    def generate_artifact(self, artifact_type: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a security artifact using Moonshot AI
        
        Args:
            artifact_type: Type of artifact to generate
            output_path: Optional custom output path
            
        Returns:
            Dict with status, artifact_type, output_path, and any errors
        """
        
        if artifact_type not in self.ARTIFACT_TEMPLATES:
            return {
                "status": "error",
                "artifact_type": artifact_type,
                "error": f"Unknown artifact type. Available: {', '.join(self.ARTIFACT_TEMPLATES.keys())}"
            }
        
        template = self.ARTIFACT_TEMPLATES[artifact_type]
        output = output_path or template["filename"]
        
        try:
            # Call Moonshot API
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a security engineer creating production-ready security artifacts."},
                    {"role": "user", "content": template["prompt"]}
                ],
                "temperature": 0.2,
                "max_tokens": 4000
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"🔧 Generating {artifact_type}...", file=sys.stderr)
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            # Extract generated content
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            
            # Create output directory if needed
            output_path_obj = Path(output)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to output
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make scripts executable
            if output.endswith('.sh'):
                os.chmod(output, 0o755)
            
            print(f"✅ Generated: {output}", file=sys.stderr)
            
            return {
                "status": "success",
                "artifact_type": artifact_type,
                "output_path": output,
                "size": len(content)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            return {
                "status": "error",
                "artifact_type": artifact_type,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            return {
                "status": "error",
                "artifact_type": artifact_type,
                "error": error_msg
            }
    
    def generate_all(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate all available security artifacts"""
        
        results = {
            "total": len(self.ARTIFACT_TEMPLATES),
            "success": 0,
            "failed": 0,
            "artifacts": []
        }
        
        for artifact_type in self.ARTIFACT_TEMPLATES.keys():
            output_path = None
            if output_dir:
                filename = self.ARTIFACT_TEMPLATES[artifact_type]["filename"]
                output_path = os.path.join(output_dir, filename)
            
            result = self.generate_artifact(artifact_type, output_path)
            results["artifacts"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results


def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Generate security artifacts using Moonshot AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available artifact types:
{chr(10).join(f"  • {name}: {template['filename']}" for name, template in SecurityArtifactGenerator.ARTIFACT_TEMPLATES.items())}

Examples:
  # Generate a specific artifact
  python generate_artifact.py trivy-scan
  
  # Generate with custom output path
  python generate_artifact.py secret-rotation --output ./custom/path.sh
  
  # Generate all artifacts
  python generate_artifact.py --all
  
  # Generate all artifacts to a specific directory
  python generate_artifact.py --all --output-dir ./security-artifacts
        """
    )
    
    parser.add_argument(
        "artifact_type",
        nargs="?",
        help="Type of artifact to generate"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Custom output path for the artifact"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all available artifacts"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for all artifacts (used with --all)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available artifact types"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # List available artifacts
    if args.list:
        print("Available artifact types:")
        for name, template in SecurityArtifactGenerator.ARTIFACT_TEMPLATES.items():
            print(f"  • {name:20s} → {template['filename']}")
        sys.exit(0)
    
    # Validate arguments
    if not args.all and not args.artifact_type:
        parser.print_help()
        sys.exit(1)
    
    try:
        generator = SecurityArtifactGenerator()
        
        if args.all:
            # Generate all artifacts
            results = generator.generate_all(args.output_dir)
            
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print("\n" + "="*60)
                print("📊 ARTIFACT GENERATION RESULTS")
                print("="*60)
                print(f"Total artifacts: {results['total']}")
                print(f"✅ Success:      {results['success']}")
                print(f"❌ Failed:       {results['failed']}")
                print("="*60)
            
            sys.exit(0 if results['failed'] == 0 else 1)
        
        else:
            # Generate single artifact
            result = generator.generate_artifact(args.artifact_type, args.output)
            
            if args.json:
                print(json.dumps(result, indent=2))
            
            sys.exit(0 if result["status"] == "success" else 1)
    
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

