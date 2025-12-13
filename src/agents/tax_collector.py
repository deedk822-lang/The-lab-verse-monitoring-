"""
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
        logger.info(f"\nGlean Status: {glean_results['status']}")
        logger.info(f"OSS Status: {oss_results['status']}")
        logger.info(f"\nTotal Sources Found: {len(all_sources)}")

        if total_revenue > 0:
            logger.info(f"\n💰 REAL REVENUE DETECTED: R{total_revenue:,.2f}")
            for source in all_sources:
                logger.info(f"   - R{source['amount_zar']:,.2f} from {source['source']}")
        else:
            logger.info(f"\n💰 REAL REVENUE DETECTED: R0.00")
            logger.info("   No tax claims found in data sources.")

        logger.info("="*60)

        return result


if __name__ == "__main__":
    agent = TaxAgentMaster()
    result = agent.execute_revenue_search()

    # Output JSON for pipeline integration
    print(json.dumps(result, indent=2))
