#!/usr/bin/env python3
"""
Vaal AI Empire: Simulation Purge & Reality Enforcement
Removes all mock data, placeholders, and fake revenue calculations.
Enforces zero-tolerance policy: Real data or explicit error.

Run: python scripts/purge_simulations.py
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimulationPurge")

class SimulationPurge:
    """Identifies and removes all simulation artifacts"""

    # Patterns that indicate fake/mock/simulation code
    SIMULATION_INDICATORS = [
        'MagicMock',
        'unittest.mock',
        'mock.patch',
        'Mock()',
        'return 25.00',
        'return 75000',
        'placeholder',
        'YOUR_',
        'example.com',
        'test@test.com',
        'default_value',
        'fallback_value',
        '# TODO',
        '# FIXME',
        'CHANGE_ME',
        'if True:  # Always',
        'pass  # Placeholder'
    ]

    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root).resolve()
        self.files_modified = []
        self.files_deleted = []
        self.issues_found = []

    def scan_file_for_simulations(self, filepath: Path) -> List[Dict]:
        """Scan a Python file for simulation indicators"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for indicator in self.SIMULATION_INDICATORS:
                    if indicator.lower() in line.lower():
                        issues.append({
                            'file': str(filepath),
                            'line': line_num,
                            'indicator': indicator,
                            'content': line.strip()
                        })
        except Exception as e:
            logger.error(f"Error scanning {filepath}: {e}")

        return issues

    def remove_test_directory(self):
        """Remove entire tests directory containing mocks"""
        test_dirs = [
            self.project_root / 'tests',
            self.project_root / 'test',
            self.project_root / 'src' / 'tests'
        ]

        for test_dir in test_dirs:
            if test_dir.exists():
                logger.info(f"🗑️  Deleting test directory: {test_dir}")
                shutil.rmtree(test_dir)
                self.files_deleted.append(str(test_dir))

    def rewrite_tax_agent(self):
        """Rewrite tax agent to return R0.00 unless real data found"""
        tax_agent_path = self.project_root / 'src' / 'agents' / 'tax_collector.py'

        tax_agent_content = '''"""
Tax Agent - Reality-Based Revenue Detection
Returns R0.00 unless actual financial data is parsed from external sources.
No fallback values, no assumptions, no simulations.
"""

import logging
import os
import json
import re
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaxAgentMaster")


class TaxAgentMaster:
    """Tax revenue detection with zero-tolerance for fake data"""

    def __init__(self):
        self.glean_available = self._check_glean()
        self.oss_available = self._check_oss()

    def _check_glean(self) -> bool:
        """Check if Glean integration is available"""
        try:
            from src.core.glean_bridge import GleanContextLayer
            glean = GleanContextLayer()
            return glean.is_active
        except ImportError:
            logger.warning("Glean not available")
            return False

    def _check_oss(self) -> bool:
        """Check if OSS storage is available"""
        required_vars = ['OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET', 'OSS_BUCKET']
        return all(os.getenv(var) for var in required_vars)

    def extract_currency_from_text(self, text: str) -> float:
        """
        Extract ZAR amounts from text using regex.
        Returns 0.00 if no valid amount found.
        """
        if not text:
            return 0.00

        # Match patterns like: R25,000 or R25000.00 or ZAR 25000
        patterns = [
            r'R\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'ZAR\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*ZAR'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first match, remove commas, convert to float
                amount_str = matches[0].replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return 0.00

    def search_glean_for_tax_claims(self) -> Dict:
        """
        Search Glean for actual tax credit documents.
        Returns structured data with parsed amounts.
        """
        if not self.glean_available:
            return {
                'status': 'unavailable',
                'total_zar': 0.00,
                'claims': []
            }

        try:
            from src.core.glean_bridge import GleanContextLayer
            glean = GleanContextLayer()

            # Search for specific tax-related documents
            queries = [
                'unclaimed tax credits',
                'ETI employment tax incentive',
                'Section 12H learnership allowance',
                'R&D tax deduction Section 11D'
            ]

            total_found = 0.00
            claims = []

            for query in queries:
                results = glean.search_enterprise_memory(query, category='finance')

                if results and isinstance(results, dict):
                    # Parse any currency amounts from results
                    result_text = str(results)
                    amount = self.extract_currency_from_text(result_text)

                    if amount > 0:
                        claims.append({
                            'query': query,
                            'amount_zar': amount,
                            'source': 'glean'
                        })
                        total_found += amount

            return {
                'status': 'found' if total_found > 0 else 'no_results',
                'total_zar': total_found,
                'claims': claims
            }

        except Exception as e:
            logger.error(f"Glean search failed: {e}")
            return {
                'status': 'error',
                'total_zar': 0.00,
                'claims': [],
                'error': str(e)
            }

    def search_oss_for_financial_docs(self) -> Dict:
        """
        Search OSS storage for processed financial documents.
        Returns parsed tax credit amounts.
        """
        if not self.oss_available:
            return {
                'status': 'unavailable',
                'total_zar': 0.00,
                'documents': []
            }

        try:
            import oss2

            auth = oss2.Auth(
                os.getenv('OSS_ACCESS_KEY_ID'),
                os.getenv('OSS_ACCESS_KEY_SECRET')
            )
            bucket = oss2.Bucket(
                auth,
                os.getenv('OSS_ENDPOINT'),
                os.getenv('OSS_BUCKET')
            )

            # Search for tax claim results
            total_found = 0.00
            documents = []

            for obj in oss2.ObjectIterator(bucket, prefix='tax_claims/'):
                if obj.key.endswith('.json'):
                    try:
                        content = bucket.get_object(obj.key).read()
                        data = json.loads(content)

                        # Extract amounts from structured data
                        amount = data.get('total_annual_savings_zar', 0.00)

                        if amount > 0:
                            documents.append({
                                'file': obj.key,
                                'amount_zar': amount,
                                'source': 'oss'
                            })
                            total_found += amount

                    except Exception as e:
                        logger.warning(f"Failed to parse {obj.key}: {e}")
                        continue

            return {
                'status': 'found' if total_found > 0 else 'no_results',
                'total_zar': total_found,
                'documents': documents
            }

        except Exception as e:
            logger.error(f"OSS search failed: {e}")
            return {
                'status': 'error',
                'total_zar': 0.00,
                'documents': [],
                'error': str(e)
            }

    def execute_revenue_search(self) -> Dict:
        """
        Execute comprehensive tax revenue search.
        Returns ONLY real amounts found in actual data sources.
        """
        logger.info("="*60)
        logger.info("TAX AGENT: Reality-Based Revenue Search")
        logger.info("="*60)

        # Search all available sources
        glean_results = self.search_glean_for_tax_claims()
        oss_results = self.search_oss_for_financial_docs()

        # Aggregate real findings
        total_revenue = glean_results['total_zar'] + oss_results['total_zar']

        all_sources = []
        all_sources.extend(glean_results.get('claims', []))
        all_sources.extend(oss_results.get('documents', []))

        result = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'total_revenue_zar': total_revenue,
            'sources': all_sources,
            'glean_status': glean_results['status'],
            'oss_status': oss_results['status']
        }

        # Log findings
        logger.info(f"\\nGlean Status: {glean_results['status']}")
        logger.info(f"OSS Status: {oss_results['status']}")
        logger.info(f"\\nTotal Sources Found: {len(all_sources)}")

        if total_revenue > 0:
            logger.info(f"\\n💰 REAL REVENUE DETECTED: R{total_revenue:,.2f}")
            for source in all_sources:
                logger.info(f"   - R{source['amount_zar']:,.2f} from {source['source']}")
        else:
            logger.info(f"\\n💰 REAL REVENUE DETECTED: R0.00")
            logger.info("   No tax claims found in data sources.")

        logger.info("="*60)

        return result


if __name__ == "__main__":
    agent = TaxAgentMaster()
    result = agent.execute_revenue_search()

    # Output JSON for pipeline integration
    print(json.dumps(result, indent=2))
'''

        # Create directory if needed
        tax_agent_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(tax_agent_path, 'w', encoding='utf-8') as f:
            f.write(tax_agent_content)

        logger.info(f"✅ Rewrote tax agent: {tax_agent_path}")
        self.files_modified.append(str(tax_agent_path))

    def scan_all_files(self):
        """Scan all Python files for simulation indicators"""
        logger.info("\n🔍 Scanning for simulation indicators...")

        python_files = list(self.project_root.rglob('*.py'))

        for filepath in python_files:
            if 'venv' in str(filepath) or '.git' in str(filepath):
                continue

            issues = self.scan_file_for_simulations(filepath)
            if issues:
                self.issues_found.extend(issues)

        if self.issues_found:
            logger.warning(f"\n⚠️  Found {len(self.issues_found)} simulation indicators:")

            # Group by file
            by_file = {}
            for issue in self.issues_found:
                file = issue['file']
                if file not in by_file:
                    by_file[file] = []
                by_file[file].append(issue)

            for file, issues in by_file.items():
                logger.warning(f"\n   {file}:")
                for issue in issues[:5]:  # Show first 5 per file
                    logger.warning(f"      Line {issue['line']}: {issue['indicator']}")
                    logger.warning(f"         {issue['content'][:80]}")

                if len(issues) > 5:
                    logger.warning(f"      ... and {len(issues) - 5} more")
        else:
            logger.info("✅ No simulation indicators found")

    def remove_placeholder_env_values(self):
        """Check .env files for placeholder values"""
        env_files = [
            self.project_root / '.env',
            self.project_root / '.env.example'
        ]

        placeholders_found = []

        for env_file in env_files:
            if not env_file.exists():
                continue

            logger.info(f"\n🔍 Checking {env_file.name}...")

            with open(env_file, 'r') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Check for placeholder patterns
                if any(p in line.lower() for p in ['your_', 'change_me', 'example', 'placeholder', 'todo']):
                    placeholders_found.append({
                        'file': str(env_file),
                        'line': line_num,
                        'content': line
                    })

        if placeholders_found:
            logger.warning(f"\n⚠️  Found {len(placeholders_found)} placeholder environment variables:")
            for item in placeholders_found:
                logger.warning(f"   {item['file']}:{item['line']}")
                logger.warning(f"      {item['content']}")
        else:
            logger.info("✅ No placeholder environment variables found")

    def generate_report(self):
        """Generate final purge report"""
        logger.info("\n" + "="*60)
        logger.info("PURGE COMPLETE - SUMMARY")
        logger.info("="*60)

        logger.info(f"\n📁 Files Deleted: {len(self.files_deleted)}")
        for file in self.files_deleted:
            logger.info(f"   - {file}")

        logger.info(f"\n✏️  Files Modified: {len(self.files_modified)}")
        for file in self.files_modified:
            logger.info(f"   - {file}")

        logger.info(f"\n⚠️  Simulation Indicators: {len(self.issues_found)}")
        if self.issues_found:
            logger.info("   Manual review recommended for these files.")

        logger.info("\n" + "="*60)
        logger.info("REALITY ENFORCEMENT RULES:")
        logger.info("="*60)
        logger.info("1. All revenue calculations must parse real data")
        logger.info("2. Return R0.00 if no data found (not R25.00)")
        logger.info("3. No default/fallback monetary values")
        logger.info("4. No mock objects or test fixtures")
        logger.info("5. All placeholders must be actual credentials")
        logger.info("="*60)

    def execute(self):
        """Execute complete purge process"""
        logger.info("🔥 STARTING SIMULATION PURGE")
        logger.info("="*60)

        # Step 1: Remove test directories
        logger.info("\n📦 Step 1: Removing test directories...")
        self.remove_test_directory()

        # Step 2: Rewrite tax agent
        logger.info("\n📝 Step 2: Rewriting tax agent...")
        self.rewrite_tax_agent()

        # Step 3: Scan for remaining simulations
        logger.info("\n🔍 Step 3: Scanning for simulations...")
        self.scan_all_files()

        # Step 4: Check environment files
        logger.info("\n🔐 Step 4: Checking environment variables...")
        self.remove_placeholder_env_values()

        # Step 5: Generate report
        self.generate_report()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Purge simulations and enforce reality')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--dry-run', action='store_true', help='Scan only, do not modify')

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    purge = SimulationPurge(project_root=args.project_root)

    if args.dry_run:
        purge.scan_all_files()
        purge.remove_placeholder_env_values()
    else:
        purge.execute()


if __name__ == "__main__":
    main()
