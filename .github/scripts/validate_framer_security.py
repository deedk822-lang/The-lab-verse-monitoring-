#!/usr/bin/env python3
"""
Framer No-Code Security Validator
Catches logical errors and security issues specific to Framer integrations
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
import subprocess

def annotate_github(level: str, message: str, file: str, line: int = None):
    """Create GitHub Actions annotation"""
    line_str = f",line={line}" if line else ""
    print(f"::{level} file={file}{line_str}::{message}")

class FramerSecurityValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_proxy_ssrf(self, file_path: str) -> List[Dict]:
        """
        Detect SSRF vulnerabilities in proxy endpoints
        Issue: Using startsWith() for domain validation
        """
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Pattern 1: startsWith() vulnerability
            for i, line in enumerate(lines, 1):
                if re.search(r'\.startsWith\([\'"]https?://[^\'"]+[\'"]\)', line):
                    if 'endpoint' in line or 'url' in line.lower():
                        findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'error',
                            'message': 'SSRF vulnerability: startsWith() can be bypassed. Use URL.hostname instead',
                            'code': line.strip(),
                            'cwe': 'CWE-918'
                        })

            # Pattern 2: Missing hostname validation
            has_url_parse = 'new URL(' in content
            has_fetch_proxy = 'fetch(' in content and '/api/' in file_path

            if has_fetch_proxy and not has_url_parse:
                findings.append({
                    'file': file_path,
                    'line': 1,
                    'severity': 'warning',
                    'message': 'Proxy endpoint lacks URL parsing for security validation',
                    'code': None
                })

        except Exception as e:
            print(f"Error validating {file_path}: {e}")

        return findings

    def validate_env_config_sync(self) -> List[Dict]:
        """
        Check if NEXT_PUBLIC_ vars in code match vercel.json
        Issue: Variables used in code but missing from build.env
        """
        findings = []

        # Extract vars from vercel.json
        vercel_vars = set()
        try:
            with open('vercel.json', 'r') as f:
                vercel_config = json.load(f)
                build_env = vercel_config.get('build', {}).get('env', {})
                vercel_vars = set(build_env.keys())
        except FileNotFoundError:
            findings.append({
                'file': 'vercel.json',
                'line': 1,
                'severity': 'error',
                'message': 'vercel.json not found - required for Framer deployments'
            })
            return findings

        # Scan code for NEXT_PUBLIC_ usage
        code_vars = set()
        for file_path in Path('src').rglob('*.{js,jsx,ts,tsx}'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find process.env.NEXT_PUBLIC_*
                    matches = re.findall(r'process\.env\.(NEXT_PUBLIC_\w+)', content)
                    code_vars.update(matches)
            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)
                continue


        # Find missing variables
        missing = code_vars - vercel_vars
        for var in missing:
            findings.append({
                'file': 'vercel.json',
                'line': 1,
                'severity': 'error',
                'message': f'Variable {var} used in code but not defined in vercel.json build.env',
                'code': f'Add: "{var}": "@{var.lower().replace("next_public_", "")}"'
            })

        return findings

    def validate_ai_output_flow(self) -> List[Dict]:
        """
        Detect dead-end data flows in AI scripts
        Issue: AI outputs to stdout but next step can't read it
        """
        findings = []

        # Check if workflow uses AI script output
        workflow_files = Path('.github/workflows').glob('*.yml')

        for wf_file in workflow_files:
            try:
                with open(wf_file, 'r') as f:
                    content = f.read()

                # Pattern: Script runs but output not captured
                if 'kimi-cms-sync.py' in content or 'moonshot' in content.lower():
                    if 'GITHUB_OUTPUT' not in content:
                        findings.append({
                            'file': str(wf_file),
                            'line': 1,
                            'severity': 'error',
                            'message': 'AI script output not captured. Use GITHUB_OUTPUT to pass data between steps',
                            'code': 'with open(os.environ["GITHUB_OUTPUT"], "a") as f: print(f"body={output}", file=f)'
                        })

            except Exception:
                continue

        return findings

    def validate_secret_masking(self) -> List[Dict]:
        """
        Check if secrets are masked in CI logs
        Issue: Traceback might expose MOONSHOT_API_KEY
        """
        findings = []

        workflow_files = Path('.github/workflows').glob('*.yml')

        for wf_file in workflow_files:
            try:
                with open(wf_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')

                # Find secret usage
                secret_lines = [i for i, line in enumerate(lines, 1)
                               if 'secrets.' in line]

                for line_num in secret_lines:
                    # Check if add-mask exists before secret usage
                    preceding_lines = lines[max(0, line_num-10):line_num]
                    has_mask = any('add-mask' in line for line in preceding_lines)

                    if not has_mask:
                        findings.append({
                            'file': str(wf_file),
                            'line': line_num,
                            'severity': 'warning',
                            'message': 'Secret used without masking. Add ::add-mask:: before usage',
                            'code': 'echo "::add-mask::${{ secrets.SECRET_NAME }}"'
                        })

            except Exception:
                continue

        return findings

    def run_all_validations(self) -> int:
        """Run all validation checks"""
        all_findings = []

        print("🔍 Running Framer Security Validations...")

        # 1. SSRF checks in proxy files
        print("\n1️⃣ Checking for SSRF vulnerabilities...")
        proxy_files = list(Path('.').rglob('**/api/**proxy*.{js,ts}'))
        for file in proxy_files:
            findings = self.validate_proxy_ssrf(str(file))
            all_findings.extend(findings)

        # 2. Environment variable sync
        print("2️⃣ Validating environment configuration...")
        all_findings.extend(self.validate_env_config_sync())

        # 3. AI data flow
        print("3️⃣ Checking AI script outputs...")
        all_findings.extend(self.validate_ai_output_flow())

        # 4. Secret masking
        print("4️⃣ Validating secret protection...")
        all_findings.extend(self.validate_secret_masking())

        # Report findings
        errors = [f for f in all_findings if f['severity'] == 'error']
        warnings = [f for f in all_findings if f['severity'] == 'warning']

        print(f"\n📊 Results: {len(errors)} errors, {len(warnings)} warnings")

        # Create GitHub annotations
        for finding in all_findings:
            annotate_github(
                finding['severity'],
                finding['message'],
                finding['file'],
                finding.get('line')
            )

        # Generate summary
        if errors or warnings:
            print("\n" + "="*60)
            print("🛡️ FRAMER SECURITY VALIDATION SUMMARY")
            print("="*60)

            if errors:
                print(f"\n❌ ERRORS ({len(errors)}):")
                for err in errors:
                    print(f"  • {err['file']}: {err['message']}")

            if warnings:
                print(f"\n⚠️  WARNINGS ({len(warnings)}):")
                for warn in warnings:
                    print(f"  • {warn['file']}: {warn['message']}")
        else:
            print("\n✅ All Framer security checks passed!")

        return 1 if errors else 0

def main():
    validator = FramerSecurityValidator()
    exit_code = validator.run_all_validations()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
