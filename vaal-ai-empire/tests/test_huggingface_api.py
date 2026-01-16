
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.huggingface_api import HuggingFaceAPI

class TestHuggingFaceAPISession(unittest.TestCase):

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"})
    @patch('requests.Session.post')
    def test_generate_uses_session(self, mock_post):
        """Verify that the generate method uses the session object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "test"}]
        mock_post.return_value = mock_response

        with HuggingFaceAPI() as client:
            client.generate("test prompt")

        mock_post.assert_called_once()

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"})
    @patch('requests.Session.post')
    def test_embed_uses_session(self, mock_post):
        """Verify that the embed method uses the session object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embeddings": []}
        mock_post.return_value = mock_response

        with HuggingFaceAPI() as client:
            client.embed(["test text"])

        mock_post.assert_called_once()

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"})
    @patch('requests.Session.post')
    def test_summarize_uses_session(self, mock_post):
        """Verify that the summarize method uses the session object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"summary_text": "summary"}]
        mock_post.return_value = mock_response

        with HuggingFaceAPI() as client:
            client.summarize("test text")

        mock_post.assert_called_once()

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"})
    @patch('requests.post')
    @patch('requests.Session.post')
    def test_check_model_status_uses_session(self, mock_session_post, mock_direct_post):
        """Verify that check_model_status now uses the session object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session_post.return_value = mock_response

        with HuggingFaceAPI() as client:
            client.check_model_status("test-model")

        mock_session_post.assert_called_once()
        mock_direct_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()
