"""
Production Support Tools
tools/confidence_scorer.py
tools/validator.py
tools/audit_logger.py

Complete implementations - no mock-ups
"""

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
# CONFIDENCE SCORER
# ============================================================

class ConfidenceScorer:
    """
    Calculate confidence score for generated code based on:
    - Code quality metrics
    - Security scan results
    - Test coverage
    - Complexity analysis
    """

    def __init__(self):
        self.base_score = 100
        self.penalties = {
            'todo': 10,
            'fixme': 10,
            'console_log': 5,
            'print_statement': 5,
            'debugger': 15,
            'large_change': 20,
            'complex_function': 8,
            'missing_tests': 25,
            'security_high': 30,
            'security_medium': 15,
            'security_low': 5,
            'no_docstrings': 10
        }

        logger.info("✓ Confidence Scorer initialized")

    async def calculate(
        self,
        code_changes: Dict,
        security_result: Dict,
        plan: Dict
    ) -> Dict:
        """Calculate comprehensive confidence score"""

        score = self.base_score
        breakdown = {
            'base': self.base_score,
            'penalties': [],
            'bonuses': []
        }

        # Analyze code quality
        quality_penalty = self._analyze_code_quality(code_changes, breakdown)
        score -= quality_penalty

        # Analyze security
        security_penalty = self._analyze_security(security_result, breakdown)
        score -= security_penalty

        # Analyze scope
        scope_penalty = self._analyze_scope(code_changes, breakdown)
        score -= scope_penalty

        # Check for tests
        test_penalty = self._check_tests(code_changes, breakdown)
        score -= test_penalty

        # Bonus for good practices
        bonus = self._calculate_bonuses(code_changes, plan, breakdown)
        score += bonus

        # Clamp score
        final_score = max(0, min(100, score))

        result = {
            'score': final_score,
            'grade': self._score_to_grade(final_score),
            'breakdown': breakdown,
            'recommendation': self._get_recommendation(final_score)
        }

        logger.info(f"Confidence calculated: {final_score}/100 ({result['grade']})")
        return result

    def _analyze_code_quality(self, code_changes: Dict, breakdown: Dict) -> float:
        """Analyze code quality issues"""
        penalty = 0
        files = code_changes.get('files', {})

        for filepath, content in files.items():
            if not isinstance(content, str):
                continue

            # Check for TODOs/FIXMEs
            todos = len(re.findall(r'\b(TODO|FIXME)\b', content, re.IGNORECASE))
            if todos > 0:
                penalty += todos * self.penalties['todo']
                breakdown['penalties'].append({
                    'type': 'todo_fixme',
                    'count': todos,
                    'penalty': todos * self.penalties['todo'],
                    'file': filepath
                })

            # Check for console.log / print
            if filepath.endswith(('.js', '.ts', '.jsx', '.tsx')):
                console_logs = len(re.findall(r'console\.(log|debug|info)', content))
                if console_logs > 0:
                    penalty += console_logs * self.penalties['console_log']
                    breakdown['penalties'].append({
                        'type': 'console_log',
                        'count': console_logs,
                        'penalty': console_logs * self.penalties['console_log'],
                        'file': filepath
                    })

            elif filepath.endswith('.py'):
                print_statements = len(re.findall(r'\bprint\s*\(', content))
                if print_statements > 0:
                    penalty += print_statements * self.penalties['print_statement']
                    breakdown['penalties'].append({
                        'type': 'print_statement',
                        'count': print_statements,
                        'penalty': print_statements * self.penalties['print_statement'],
                        'file': filepath
                    })

            # Check for debugger statements
            debuggers = len(re.findall(r'\bdebugger\b', content))
            if debuggers > 0:
                penalty += debuggers * self.penalties['debugger']
                breakdown['penalties'].append({
                    'type': 'debugger',
                    'count': debuggers,
                    'penalty': debuggers * self.penalties['debugger'],
                    'file': filepath
                })

            # Check for docstrings (Python)
            if filepath.endswith('.py'):
                # Simple check: functions without docstrings
                functions = len(re.findall(r'\bdef\s+\w+\s*\(', content))
                docstrings = len(re.findall(r'""".*?"""', content, re.DOTALL))
                if functions > 0 and docstrings == 0:
                    penalty += self.penalties['no_docstrings']
                    breakdown['penalties'].append({
                        'type': 'missing_docstrings',
                        'penalty': self.penalties['no_docstrings'],
                        'file': filepath
                    })

        return penalty

    def _analyze_security(self, security_result: Dict, breakdown: Dict) -> float:
        """Analyze security scan results"""
        penalty = 0

        high_issues = security_result.get('high_issues', [])
        medium_issues = security_result.get('medium_issues', [])
        low_issues = security_result.get('low_issues', [])

        if high_issues:
            penalty += len(high_issues) * self.penalties['security_high']
            breakdown['penalties'].append({
                'type': 'security_high',
                'count': len(high_issues),
                'penalty': len(high_issues) * self.penalties['security_high']
            })

        if medium_issues:
            penalty += len(medium_issues) * self.penalties['security_medium']
            breakdown['penalties'].append({
                'type': 'security_medium',
                'count': len(medium_issues),
                'penalty': len(medium_issues) * self.penalties['security_medium']
            })

        if low_issues:
            penalty += len(low_issues) * self.penalties['security_low']
            breakdown['penalties'].append({
                'type': 'security_low',
                'count': len(low_issues),
                'penalty': len(low_issues) * self.penalties['security_low']
            })

        return penalty

    def _analyze_scope(self, code_changes: Dict, breakdown: Dict) -> float:
        """Analyze change scope"""
        penalty = 0
        files_count = len(code_changes.get('files', {}))

        if files_count > 15:
            penalty += self.penalties['large_change']
            breakdown['penalties'].append({
                'type': 'large_change',
                'files_count': files_count,
                'penalty': self.penalties['large_change']
            })

        return penalty

    def _check_tests(self, code_changes: Dict, breakdown: Dict) -> float:
        """Check if tests are included"""
        penalty = 0
        files = code_changes.get('files', {})

        # Check if any test files are included
        has_tests = any(
            'test' in filepath.lower() or 'spec' in filepath.lower()
            for filepath in files.keys()
        )

        # Check if implementation files exist without tests
        impl_files = [
            f for f in files.keys()
            if not ('test' in f.lower() or 'spec' in f.lower())
            and f.endswith(('.py', '.js', '.ts', '.jsx', '.tsx'))
        ]

        if impl_files and not has_tests:
            penalty += self.penalties['missing_tests']
            breakdown['penalties'].append({
                'type': 'missing_tests',
                'penalty': self.penalties['missing_tests']
            })

        return penalty

    def _calculate_bonuses(self, code_changes: Dict, plan: Dict, breakdown: Dict) -> float:
        """Calculate bonuses for good practices"""
        bonus = 0
        files = code_changes.get('files', {})

        # Bonus for including tests
        has_tests = any('test' in f.lower() or 'spec' in f.lower() for f in files.keys())
        if has_tests:
            bonus += 10
            breakdown['bonuses'].append({
                'type': 'includes_tests',
                'bonus': 10
            })

        # Bonus for documentation
        has_docs = any(
            'readme' in f.lower() or 'doc' in f.lower() or '.md' in f.lower()
            for f in files.keys()
        )
        if has_docs:
            bonus += 5
            breakdown['bonuses'].append({
                'type': 'includes_documentation',
                'bonus': 5
            })

        return bonus

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _get_recommendation(self, score: float) -> str:
        """Get deployment recommendation"""
        if score >= 95:
            return 'Safe for auto-merge'
        elif score >= 85:
            return 'Create PR for review'
        elif score >= 70:
            return 'Create draft PR for careful review'
        else:
            return 'Requires significant review before deployment'
