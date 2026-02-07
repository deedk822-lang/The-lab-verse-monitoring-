import unittest
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Attempt import of the actual module
try:
    from rainmaker_orchestrator import RainmakerOrchestrator, DirectiveParser, ToolType
    print("✅ Successfully imported rainmaker_orchestrator in test script")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

class TestRainmakerOrchestrator(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(RainmakerOrchestrator)

    def test_directive_parser(self):
        # Example: Test if 'grok' maps correctly
        tool, prompt = DirectiveParser.parse("grok search for news")
        self.assertEqual(tool, ToolType.GROK)

if __name__ == "__main__":
    unittest.main()
