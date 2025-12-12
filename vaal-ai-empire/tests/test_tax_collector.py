import sys
import os
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.tax_collector import TaxAgentMaster

def test_tax_agent_master_instantiation():
    """
    Tests that the TaxAgentMaster class can be instantiated without errors.
    """
    try:
        agent = TaxAgentMaster()
        assert agent is not None
    except Exception as e:
        pytest.fail(f"Failed to instantiate TaxAgentMaster: {e}")
