import unittest
import os
from unittest.mock import patch

# Adjust the Python path to ensure 'agents' can be found
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autogen import LLMConfig
from agents.ag2.orchestrator import VaalAIEmpireOrchestrator

class TestOrchestratorConfig(unittest.TestCase):

    @patch.dict(os.environ, {"OPENAI_MODEL": "test-model-from-env", "OPENAI_API_KEY": "test-key-from-env"})
    @patch("agents.ag2.orchestrator.LLMConfig.from_json")
    def test_load_from_env_vars_when_file_fails(self, mock_from_json):
        """
        Tests if the orchestrator loads configuration from environment variables
        when the OAI_CONFIG_LIST file is not found.
        """
        # Simulate file not found
        mock_from_json.side_effect = ValueError("File not found")

        orchestrator = VaalAIEmpireOrchestrator()
        config_list = orchestrator.llm_config.config_list

        self.assertEqual(len(config_list), 1)
        self.assertEqual(config_list[0]["model"], "test-model-from-env")
        self.assertEqual(config_list[0]["api_key"], "test-key-from-env")

    @patch("agents.ag2.orchestrator.LLMConfig.from_json")
    def test_load_from_file_successfully(self, mock_from_json):
        """
        Tests if the orchestrator successfully loads configuration from the
        OAI_CONFIG_LIST file.
        """
        # Simulate successful file loading by returning a valid LLMConfig instance
        mock_from_json.return_value = LLMConfig(config_list=[{"model": "file-model", "api_key": "file-key"}])

        orchestrator = VaalAIEmpireOrchestrator()
        config_list = orchestrator.llm_config.config_list

        self.assertEqual(len(config_list), 1)
        self.assertEqual(config_list[0]["model"], "file-model")
        self.assertEqual(config_list[0]["api_key"], "file-key")
        mock_from_json.assert_called_once_with(env_or_file="OAI_CONFIG_LIST")

    @patch.dict(os.environ, {}, clear=True)
    @patch("agents.ag2.orchestrator.LLMConfig.from_json")
    def test_fallback_to_dummy_config(self, mock_from_json):
        """
        Tests if the orchestrator falls back to a dummy configuration when
        both the file and environment variables are missing.
        """
        # Simulate file not found and no env vars
        mock_from_json.side_effect = ValueError("File not found")

        orchestrator = VaalAIEmpireOrchestrator()
        config_list = orchestrator.llm_config.config_list

        self.assertEqual(len(config_list), 1)
        self.assertEqual(config_list[0]["model"], "gpt-4")
        self.assertEqual(config_list[0]["api_key"], "dummy")

if __name__ == "__main__":
    unittest.main()
