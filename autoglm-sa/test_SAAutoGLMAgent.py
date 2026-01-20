import unittest
from unittest.mock import patch
from SAAutoGLMAgent import SAAutoGLMAgent

class TestSAAutoGLMAgent(unittest.TestCase):

    @patch('SAAutoGLMAgent.SAAutoGLMAgent.check_internet', return_value=False)
    @patch('os.path.exists', return_value=False)
    def test_get_optimal_config_offline(self, mock_exists, mock_check_internet):
        agent = SAAutoGLMAgent()
        config = agent.get_optimal_config()
        self.assertEqual(config['mode'], 'offline')

    @patch('SAAutoGLMAgent.SAAutoGLMAgent.check_internet', return_value=True)
    @patch('os.path.exists', return_value=False)
    def test_get_optimal_config_cloud(self, mock_exists, mock_check_internet):
        agent = SAAutoGLMAgent()
        config = agent.get_optimal_config()
        self.assertEqual(config['mode'], 'cloud')

    @patch('os.path.exists', return_value=True)
    def test_get_optimal_config_local(self, mock_exists):
        agent = SAAutoGLMAgent()
        config = agent.get_optimal_config()
        self.assertEqual(config['mode'], 'local')

if __name__ == '__main__':
    unittest.main()
