# scripts/test_all.py - 修复版
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# --- Path Setup ---
# Add root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ⭐ 修复：删除不存在的 vaal-ai-empire 路径

# --- Import Actually Existing Modules ---
# ✅ content_generator 存在
from services.content_generator import ContentFactory

# ⭐ 删除不存在的导入
# from autogen import LLMConfig  # 未在 requirements.txt 中
# from agents.ag2.orchestrator import VaalAIEmpireOrchestrator  # 不存在

class TestContentFactory(unittest.TestCase):
    """测试 ContentFactory（实际存在的模块）"""

    @patch.dict(os.environ, {"KIMI_API_BASE": "http://mock-vllm-endpoint:8000/v1"})
    @patch("services.content_generator.OpenAI")
    def test_content_generation(self, mock_openai_client):
        """测试内容生成功能"""
        # Arrange
        mock_client = mock_openai_client.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_client.chat.completions.create.return_value = mock_response

        # Act
        factory = ContentFactory()
        result = factory.generate_content("test prompt")

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["provider"], "kimi")
        self.assertEqual(result["text"], "Test content")


class TestOrchestratorIntegration(unittest.TestCase):
    """测试 Rainmaker Orchestrator 集成"""

    @patch("rainmaker_orchestrator.httpx.AsyncClient")
    def test_orchestrator_directive_parsing(self, mock_client):
        """测试指令解析"""
        from rainmaker_orchestrator import DirectiveParser

        # 测试关键词识别
        tool, prompt = DirectiveParser.parse("analyze the history")
        self.assertEqual(tool.value, "kimi")

        tool, prompt = DirectiveParser.parse("search for news")
        self.assertEqual(tool.value, "grok")


if __name__ == "__main__":
    unittest.main()