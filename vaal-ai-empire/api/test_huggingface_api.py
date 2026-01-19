import unittest
from unittest.mock import patch, MagicMock
import os
from api.huggingface_api import HuggingFaceAPI

class TestHuggingFaceAPI(unittest.TestCase):

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test_token"})
    def setUp(self):
        self.api = HuggingFaceAPI()

    def tearDown(self):
        self.api.close()

    @patch('requests.Session.post')
    def test_check_model_status_uses_session(self, mock_post):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        model_name = "test-model"

        # Act
        result = self.api.check_model_status(model_name)

        # Assert
        mock_post.assert_called_once()
        self.assertEqual(result['status'], 'ready')

if __name__ == '__main__':
    unittest.main()
