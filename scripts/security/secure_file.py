#!/usr/bin/env python3
"""
Security Hardening Script using Moonshot AI (Kimi)
Auto-generates secure code & configs by sending files to Kimi for hardening.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class MoonshotSecurityHardener:
    """Hardens files using Moonshot AI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY environment variable not set")
        
        self.api_url = "https://api.moonshot.ai/v1/chat/completions"
        self.model = "moonshot-v1-8k"
        
    def _build_security_prompt(self, file_path: str, content: str) -> str:
        """Build context-aware security prompt based on file type"""
        
        file_ext = Path(file_path).suffix.lower()
        
        # Base security principles
        base_prompt = """You are a security engineer specializing in OWASP best practices and secure coding.

Your task: Return ONLY the patched file content with security hardening applied. NO explanations, NO markdown code blocks, NO commentary.

Apply these security principles:
"""
        
        # File-type specific hardening rules
        if file_ext in ['.py']:
            specific_rules = """
Python Security:
- Remove hardcoded credentials, API keys, secrets
- Use environment variables for sensitive data
- Add input validation and sanitization
- Implement proper error handling (no sensitive info in errors)
- Use parameterized queries for database operations
- Add rate limiting where applicable
- Implement proper authentication/authorization checks
- Use secure random number generation (secrets module)
- Validate file paths to prevent directory traversal
- Set secure defaults for all configurations
"""
        elif file_ext in ['.yml', '.yaml']:
            specific_rules = """
YAML/Docker Compose Security:
- Remove hardcoded passwords and secrets
- Use Docker secrets or environment variables
- Set resource limits (memory, CPU)
- Run containers as non-root user
- Use read-only file systems where possible
- Disable unnecessary capabilities
- Set security_opt (no-new-privileges, seccomp, apparmor)
- Use specific image tags (not 'latest')
- Enable health checks
- Set proper network isolation
- Add restart policies
"""
        elif 'dockerfile' in file_path.lower():
            specific_rules = """
Dockerfile Security:
- Use specific base image versions (not 'latest')
- Run as non-root user (USER directive)
- Use multi-stage builds to minimize attack surface
- Don't include secrets in image layers
- Use .dockerignore to exclude sensitive files
- Minimize number of layers
- Scan for vulnerabilities
- Set proper file permissions
- Use COPY instead of ADD
- Validate and sanitize build arguments
"""
        elif file_ext in ['.env', '.env.example']:
            specific_rules = """
Environment File Security:
- Remove all actual secret values (replace with placeholders)
- Add comments explaining each variable
- Use strong placeholder patterns (e.g., 'your_secret_here')
- Document required vs optional variables
- Add security warnings for sensitive values
- Suggest using secret management tools
"""
        elif file_ext in ['.sh', '.bash']:
            specific_rules = """
Shell Script Security:
- Validate all inputs
- Quote variables properly
- Use 'set -euo pipefail' for error handling
- Avoid eval and command substitution with untrusted input
- Check file permissions before operations
- Use absolute paths
- Implement proper logging
- Add timeout mechanisms
"""
        elif file_ext in ['.js', '.ts']:
            specific_rules = """
JavaScript/TypeScript Security:
- Remove hardcoded credentials
- Validate and sanitize all inputs
- Use parameterized queries
- Implement proper CORS policies
- Add rate limiting
- Use secure session management
- Implement CSRF protection
- Avoid eval() and Function() constructor
- Use Content Security Policy headers
- Implement proper error handling
"""
        elif file_ext in ['.go']:
            specific_rules = """
Go Security:
- Remove hardcoded credentials
- Use context for timeouts and cancellation
- Validate inputs thoroughly
- Use prepared statements for SQL
- Implement proper error handling
- Use crypto/rand for random generation
- Set proper HTTP timeouts
- Implement rate limiting
- Use secure TLS configurations
"""
        else:
            specific_rules = """
General Security:
- Remove hardcoded credentials and secrets
- Add input validation
- Implement proper error handling
- Use secure defaults
- Add security comments where needed
- Follow principle of least privilege
"""
        
        return base_prompt + specific_rules + f"\n\nOriginal file ({file_path}):\n\n"
    
    def harden_file(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Harden a single file using Moonshot AI
        
        Args:
            file_path: Path to file to harden
            output_path: Optional output path (defaults to overwriting original)
            
        Returns:
            Dict with status, original_path, output_path, and any errors
        """
        
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Build security prompt
            system_prompt = self._build_security_prompt(file_path, original_content)
            
            # Call Moonshot API
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": original_content}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"🔒 Hardening {file_path}...", file=sys.stderr)
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            # Extract hardened content
            result = response.json()
            hardened_content = result["choices"][0]["message"]["content"].strip()
            
            # Remove markdown code blocks if present
            if hardened_content.startswith("```"):
                lines = hardened_content.split("\n")
                # Remove first line (```language) and last line (```)
                hardened_content = "\n".join(lines[1:-1]) if len(lines) > 2 else hardened_content
            
            # Write to output
            output = output_path or file_path
            with open(output, 'w', encoding='utf-8') as f:
                f.write(hardened_content)
            
            print(f"✅ Hardened: {output}", file=sys.stderr)
            
            return {
                "status": "success",
                "original_path": file_path,
                "output_path": output,
                "original_size": len(original_content),
                "hardened_size": len(hardened_content)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            return {
                "status": "error",
                "original_path": file_path,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            return {
                "status": "error",
                "original_path": file_path,
                "error": error_msg
            }


def main():
    """CLI entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: secure_file.py <file_path> [output_path]", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  python secure_file.py docker-compose.yml", file=sys.stderr)
        print("  python secure_file.py config.py config.secure.py", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        hardener = MoonshotSecurityHardener()
        result = hardener.harden_file(file_path, output_path)
        
        # Print result as JSON to stdout
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "success" else 1)
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

