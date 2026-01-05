import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess

logger = logging.getLogger(__name__)

# ============================================================
# SECURITY VALIDATOR
# ============================================================

class SecurityValidator:
    """Run security validation on code changes"""

    def __init__(self):
        self.critical_patterns = [
            (r'password\s*=\s*["\'](?!<%|\{\{).+?["\']', 'Hardcoded password'),
            (r'api[_-]?key\s*=\s*["\'](?!<%|\{\{).+?["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'](?!<%|\{\{).+?["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\'](?!<%|\{\{).+?["\']', 'Hardcoded token'),
            (r'eval\s*\(', 'Use of eval()'),
            (r'exec\s*\(', 'Use of exec()'),
        ]

        logger.info("✓ Security Validator initialized")

    async def validate(self, code_changes: Dict) -> Dict:
        """Run security validation"""

        result = {
            'critical_issues': [],
            'high_issues': [],
            'medium_issues': [],
            'low_issues': [],
            'passed': True
        }

        files = code_changes.get('files', {})

        for filepath, content in files.items():
            if not isinstance(content, str):
                continue

            # Check critical patterns
            for pattern, description in self.critical_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    result['critical_issues'].append({
                        'file': filepath,
                        'line': line_num,
                        'issue': description,
                        'snippet': match.group()[:50]
                    })
                    result['passed'] = False

            # Check for SQL injection risks
            sql_patterns = [
                (r'execute\s*\(\s*["\'].*?\+.*?["\']', 'Potential SQL injection'),
                (r'cursor\.execute\s*\(.*?\+', 'Potential SQL injection')
            ]

            for pattern, description in sql_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    result['high_issues'].append({
                        'file': filepath,
                        'line': line_num,
                        'issue': description
                    })

        # Try to run semgrep if available
        try:
            semgrep_result = await self._run_semgrep(files)
            if semgrep_result:
                result['high_issues'].extend(semgrep_result.get('high', []))
                result['medium_issues'].extend(semgrep_result.get('medium', []))
                result['low_issues'].extend(semgrep_result.get('low', []))
        except Exception as e:
            logger.warning(f"Semgrep not available: {str(e)}")

        if result['critical_issues']:
            result['passed'] = False

        logger.info(f"Security validation: {len(result['critical_issues'])} critical, "
                   f"{len(result['high_issues'])} high, {len(result['medium_issues'])} medium")

        return result

    async def _run_semgrep(self, files: Dict) -> Optional[Dict]:
        """Run semgrep if available"""
        try:
            # Check if semgrep is installed
            result = subprocess.run(
                ['semgrep', '--version'],
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                return None

            # Write files to temp location
            temp_dir = Path('.jules/temp/security-scan')
            temp_dir.mkdir(parents=True, exist_ok=True)

            for filepath, content in files.items():
                if isinstance(content, str):
                    temp_file = temp_dir / filepath
                    temp_file.parent.mkdir(parents=True, exist_ok=True)
                    temp_file.write_text(content)

            # Run semgrep
            result = subprocess.run(
                ['semgrep', '--config=auto', '--json', str(temp_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                issues = {'high': [], 'medium': [], 'low': []}

                for finding in data.get('results', []):
                    severity = finding.get('extra', {}).get('severity', 'INFO').lower()

                    issue = {
                        'file': finding.get('path', ''),
                        'line': finding.get('start', {}).get('line', 0),
                        'issue': finding.get('check_id', ''),
                        'message': finding.get('extra', {}).get('message', '')
                    }

                    if severity in ['error', 'critical']:
                        issues['high'].append(issue)
                    elif severity == 'warning':
                        issues['medium'].append(issue)
                    else:
                        issues['low'].append(issue)

                return issues

        except Exception as e:
            logger.warning(f"Semgrep execution failed: {str(e)}")

        return None
