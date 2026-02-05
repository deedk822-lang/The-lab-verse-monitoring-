
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Adjust sys.path to find the vaal-ai-empire package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.image_generation import ImageGenerator

class TestImageGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ImageGenerator()

    def test_session_initialization(self):
        self.assertIsNotNone(self.generator.session)
        import requests
        self.assertIsInstance(self.generator.session, requests.Session)

    @patch('api.image_generation.ImageGenerator.generate')
    def test_generate_batch_parallel(self, mock_generate):
        mock_generate.return_value = {"image_url": "mock_url", "provider": "mock", "cost_usd": 0.0}
        prompts = ["prompt 1", "prompt 2", "prompt 3"]

        results = self.generator.generate_batch(prompts)

        self.assertEqual(len(results), 3)
        self.assertEqual(mock_generate.call_count, 3)
        for result in results:
            self.assertEqual(result["image_url"], "mock_url")

    def test_placeholder_generation(self):
        # This tests that PIL is working and the placeholder logic is correct
        result = self.generator._create_placeholder("test prompt")
        self.assertTrue(os.path.exists(result) or result.startswith("https://"))

if __name__ == "__main__":
    unittest.main()
