import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import importlib

class TestConfig(unittest.TestCase):

    def _reload_config_module(self):
        """
        Reloads the config module to apply mocked environments.
        """
        # Define the module name and path
        module_name = 'core.config'

        # Remove the module from sys.modules to ensure it's reloaded
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Ensure the project root is in the Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Import the module using importlib
        config = importlib.import_module(module_name)
        # Reload to be absolutely sure we get the fresh version
        importlib.reload(config)
        return config

    @patch.dict(os.environ, {'COLAB_GPU': '1'}, clear=True)
    def test_colab_secret_loading(self):
        """
        Tests if secrets are loaded from Google Colab userdata when in a Colab environment.
        """
        # Mock the google.colab.userdata module
        mock_userdata = MagicMock()
        mock_userdata.get.side_effect = lambda key: 'colab_secret' if key == 'COHERE_API_KEY' else None

        # We patch sys.modules to simulate the presence of google.colab
        with patch.dict('sys.modules', {'google.colab': MagicMock(userdata=mock_userdata)}):
            config = self._reload_config_module()

            # Assert that the COHERE_API_KEY is loaded from our mock userdata
            self.assertEqual(config.settings.COHERE_API_KEY, 'colab_secret')

            # Assert that other keys remain their default values (None)
            self.assertIsNone(config.settings.GROQ_API_KEY)

    @patch.dict(os.environ, {}, clear=True)
    def test_non_colab_environment(self):
        """
        Tests that the Google Colab userdata is not used in a non-Colab environment.
        """
        # Ensure that even if a mock of google.colab exists, it's not used because the environment lacks 'COLAB_GPU'
        mock_userdata = MagicMock()
        mock_userdata.get.return_value = 'colab_secret'

        with patch.dict('sys.modules', {'google.colab': MagicMock(userdata=mock_userdata)}):
            config = self._reload_config_module()

            # Assert that no secret is loaded as we are not in a Colab environment
            self.assertIsNone(config.settings.COHERE_API_KEY)

if __name__ == '__main__':
    # Adjust the path to run the test directly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    unittest.main()
