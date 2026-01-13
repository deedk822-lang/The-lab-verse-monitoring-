import os
import unittest
from unittest.mock import patch, MagicMock

# It's necessary to add the project's root to the Python path
# to ensure that the module can be found when running the test.
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import importlib

# Use importlib to handle the hyphen in the module path
huggingface_api_module = importlib.import_module("vaal-ai-empire.api.huggingface_api")
HuggingFaceAPI = huggingface_api_module.HuggingFaceAPI

class TestHuggingFaceAPI(unittest.TestCase):

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test_token"})
    def setUp(self):
        self.api = HuggingFaceAPI()

    @patch('requests.Session.post')
    def test_generate_success(self, mock_post):
        # Mock the requests.Session.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "This is a test."}]
        mock_post.return_value = mock_response

        # Call the generate method
        result = self.api.generate("Test prompt")

        # Assert the result
        self.assertEqual(result['text'], "This is a test.")
        self.assertIn('model', result)
        # Assert that the session was used
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_embed_success(self, mock_post):
        # Mock the requests.Session.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [[0.1, 0.2, 0.3]]
        mock_post.return_value = mock_response

        # Call the embed method
        result = self.api.embed(["Test text"])

        # Assert the result
        self.assertEqual(result['embeddings'], [[0.1, 0.2, 0.3]])
        self.assertIn('model', result)
        # Assert that the session was used
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_summarize_success(self, mock_post):
        # Mock the requests.Session.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"summary_text": "This is a summary."}]
        mock_post.return_value = mock_response

        # Call the summarize method
        result = self.api.summarize("This is a long text to summarize.")

        # Assert the result
        self.assertEqual(result['summary'], "This is a summary.")
        self.assertIn('model', result)
        # Assert that the session was used
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_check_model_status_success(self, mock_post):
        # Mock the requests.Session.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the check_model_status method
        result = self.api.check_model_status("test-model")

        # Assert the result
        self.assertEqual(result['status'], "ready")
        self.assertEqual(result['status_code'], 200)
        # Assert that the session was used
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
