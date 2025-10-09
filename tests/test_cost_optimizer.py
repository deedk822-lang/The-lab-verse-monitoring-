import unittest
import numpy as np
from src.cost_intelligence.real_algorithms import detect_anomalies_zscore
from src.cost_intelligence.enhanced_optimizer import EnhancedCostOptimizer
import asyncio

class TestCostOptimizer(unittest.TestCase):

    def test_detect_anomalies_zscore_no_anomalies(self):
        """
        Test Z-score anomaly detection with normal data.
        """
        data = [10, 12, 11, 10, 13, 9, 11, 10]
        anomalies = detect_anomalies_zscore(data, threshold=3.0)
        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_zscore_with_anomalies(self):
        """
        Test Z-score anomaly detection with clear anomalies.
        """
        data = [10, 12, 11, 10, 13, 9, 11, 100]
        anomalies = detect_anomalies_zscore(data, threshold=2.0)
        self.assertIn(7, anomalies)
        self.assertEqual(len(anomalies), 1)

    def test_enhanced_optimizer_detect_anomalies(self):
        """
        Test the enhanced optimizer's anomaly detection method.
        """
        async def run_test():
            optimizer = EnhancedCostOptimizer()
            data = [10, 12, 11, 50, 13, 9, 11, 10]
            anomalies = await optimizer.detect_anomalies(data, strategy="zscore", threshold=2.0)
            self.assertEqual(anomalies, [3])

        # Run the async test
        asyncio.run(run_test())

    def test_enhanced_optimizer_unknown_strategy(self):
        """
        Test that an unknown strategy raises a ValueError.
        """
        async def run_test():
            optimizer = EnhancedCostOptimizer()
            data = [10, 12, 11, 10]
            with self.assertRaises(ValueError):
                await optimizer.detect_anomalies(data, strategy="unknown")

        # Run the async test
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()