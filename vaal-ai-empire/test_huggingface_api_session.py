# vaal-ai-empire/test_huggingface_api_session.py
import unittest
from unittest.mock import patch, Mock
import os
import sys

# Ensure the module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


# Set a dummy token for initialization
os.environ['HUGGINGFACE_TOKEN'] = 'test-token'

from api.huggingface_api import HuggingFaceAPI

class TestHuggingFaceAPISession(unittest.TestCase):
    """
    Tests the HuggingFaceAPI class to ensure its methods work correctly
    when using a requests.Session object. This is a correctness test,
    not a performance benchmark.
    """

    def setUp(self):
        """Set up the test case"""
        self.api = HuggingFaceAPI()

    def tearDown(self):
        """Tear down the test case"""
        self.api.close()

    @patch('requests.Session.post')
    def test_generate_method_uses_session(self, mock_post):
        """Verify the generate() method uses the session.post mock"""
        # Configure the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "mocked response"}]
        mock_post.return_value = mock_response

        # Call the method
        result = self.api.generate("test prompt")

        # Assertions
        mock_post.assert_called_once()
        self.assertIn("mocked response", result["text"])
        self.assertEqual(result["model"], self.api.default_model)

    @patch('requests.Session.post')
    def test_embed_method_uses_session(self, mock_post):
        """Verify the embed() method uses the session.post mock"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [[0.1, 0.2, 0.3]]
        mock_post.return_value = mock_response

        result = self.api.embed(["test text"])

        mock_post.assert_called_once()
        self.assertEqual(result["embeddings"], [[0.1, 0.2, 0.3]])

    @patch('requests.Session.post')
    def test_summarize_method_uses_session(self, mock_post):
        """Verify the summarize() method uses the session.post mock"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"summary_text": "mocked summary"}]
        mock_post.return_value = mock_response

        result = self.api.summarize("A long piece of text to summarize.")

        mock_post.assert_called_once()
        self.assertEqual(result["summary"], "mocked summary")

    @patch('requests.Session.post')
    def test_api_error_handling(self, mock_post):
        """Test that the API client correctly handles non-200 responses"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.api.generate("test prompt")

        self.assertIn("HuggingFace API error (500)", str(context.exception))

if __name__ == '__main__':
    unittest.main()
    # Clean up the env var
    del os.environ['HUGGINGFACE_TOKEN']
