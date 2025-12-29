import unittest
import asyncio
from unittest.mock import MagicMock
from autogen import LLMConfig

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.ag2.guardian_engine_agent import GuardianEngineAgent

class TestGuardianEngineAgent(unittest.TestCase):

    def setUp(self):
        """Set up a valid, dummy LLM config and an agent instance for each test."""
        self.dummy_llm_config = LLMConfig(config_list=[{"model": "gpt-4", "api_key": "dummy"}])
        self.agent = GuardianEngineAgent(self.dummy_llm_config)
        # Manually load the knowledge base for testing the tools
        self.agent._load_knowledge_base()

    def test_initialization(self):
        """Test that the agent and its tools are initialized correctly."""
        async def run_init():
            await self.agent.initialize()

        asyncio.run(run_init())

        self.assertEqual(self.agent.agent.name, "guardian_engine")
        registered_tools = self.agent.agent.function_map.keys()
        self.assertIn("assess_loadshedding_risk", registered_tools)
        self.assertIn("query_crisis_intelligence", registered_tools)
        self.assertIn("get_business_impact", registered_tools)

    def test_assess_loadshedding_risk(self):
        """Test the logic of the load-shedding risk assessment tool."""
        red_alert = self.agent.assess_loadshedding_risk(59.9, 0, 0)
        self.assertIn("🔴 RED ALERT", red_alert)
        self.assertIn("59.9%", red_alert)

        amber_alert = self.agent.assess_loadshedding_risk(64.9, 0, 0)
        self.assertIn("🟠 AMBER ALERT", amber_alert)
        self.assertIn("64.9%", amber_alert)

        green_alert = self.agent.assess_loadshedding_risk(65.0, 0, 0)
        self.assertIn("🟢 GREEN", green_alert)
        self.assertIn("65.0%", green_alert)

    def test_query_crisis_intelligence(self):
        """Test the placeholder crisis intelligence tool."""
        query = "logistics sector"
        response = self.agent.query_crisis_intelligence(query)
        self.assertIsInstance(response, str)
        self.assertIn(query, response)

    def test_get_business_impact(self):
        """Test the placeholder business impact tool."""
        sector = "manufacturing"
        stage = 4
        response = self.agent.get_business_impact(sector, stage)
        self.assertIsInstance(response, str)
        self.assertIn(sector, response)
        self.assertIn(str(stage), response)

if __name__ == '__main__':
    unittest.main()
