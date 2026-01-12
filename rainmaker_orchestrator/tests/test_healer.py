"""
Comprehensive unit tests for the SelfHealingAgent.

Tests cover alert handling, hotfix generation, error conditions,
and integration with Kimi client and orchestrator.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.clients.kimi import KimiClient
from rainmaker_orchestrator.core import RainmakerOrchestrator


class TestSelfHealingAgentInitialization:
    """Test suite for SelfHealingAgent initialization."""
    
    def test_init_with_default_clients(self):
        """Should initialize with default Kimi client and orchestrator when none provided."""
        with patch('rainmaker_orchestrator.agents.healer.KimiClient') as mock_kimi_cls, \
             patch('rainmaker_orchestrator.agents.healer.RainmakerOrchestrator') as mock_orch_cls:
            
            agent = SelfHealingAgent()
            
            assert agent.kimi_client is not None
            assert agent.orchestrator is not None
            mock_kimi_cls.assert_called_once()
            mock_orch_cls.assert_called_once()
    
    def test_init_with_custom_kimi_client(self):
        """Should use provided Kimi client instead of creating new one."""
        mock_kimi = Mock(spec=KimiClient)
        
        with patch('rainmaker_orchestrator.agents.healer.RainmakerOrchestrator') as mock_orch_cls:
            agent = SelfHealingAgent(kimi_client=mock_kimi)
            
            assert agent.kimi_client is mock_kimi
            mock_orch_cls.assert_called_once()
    
    def test_init_with_custom_orchestrator(self):
        """Should use provided orchestrator instead of creating new one."""
        mock_orchestrator = Mock(spec=RainmakerOrchestrator)
        
        with patch('rainmaker_orchestrator.agents.healer.KimiClient') as mock_kimi_cls:
            agent = SelfHealingAgent(orchestrator=mock_orchestrator)
            
            assert agent.orchestrator is mock_orchestrator
            mock_kimi_cls.assert_called_once()
    
    def test_init_with_both_custom_clients(self):
        """Should use both provided clients when both are given."""
        mock_kimi = Mock(spec=KimiClient)
        mock_orchestrator = Mock(spec=RainmakerOrchestrator)
        
        agent = SelfHealingAgent(kimi_client=mock_kimi, orchestrator=mock_orchestrator)
        
        assert agent.kimi_client is mock_kimi
        assert agent.orchestrator is mock_orchestrator


class TestSelfHealingAgentHandleAlert:
    """Test suite for alert handling functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.mock_kimi = Mock(spec=KimiClient)
        self.mock_orchestrator = Mock(spec=RainmakerOrchestrator)
        self.agent = SelfHealingAgent(
            kimi_client=self.mock_kimi,
            orchestrator=self.mock_orchestrator
        )
    
    def test_handle_alert_success(self):
        """Should generate hotfix successfully for valid alert."""
        # Arrange
        alert = {
            'description': 'NullPointerException in payment service',
            'service': 'payment-api'
        }
        expected_blueprint = 'def fix_null_pointer():\n    # Fix implementation'
        self.mock_kimi.generate.return_value = expected_blueprint
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        assert result['blueprint'] == expected_blueprint
        self.mock_kimi.generate.assert_called_once()
        
        # Verify the prompt contains critical information
        call_args = self.mock_kimi.generate.call_args
        prompt = call_args[0][0]
        assert 'payment-api' in prompt
        assert 'NullPointerException in payment service' in prompt
        assert 'CRITICAL ALERT' in prompt
        
        # Verify hotfix mode is used
        assert call_args[1]['mode'] == 'hotfix'
    
    def test_handle_alert_with_minimal_payload(self):
        """Should handle alert with only description field."""
        # Arrange
        alert = {'description': 'Database connection timeout'}
        self.mock_kimi.generate.return_value = 'hotfix code'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        assert 'Unknown service' in self.mock_kimi.generate.call_args[0][0]
    
    def test_handle_alert_with_empty_description(self):
        """Should handle alert with empty description gracefully."""
        # Arrange
        alert = {'description': '', 'service': 'api-gateway'}
        self.mock_kimi.generate.return_value = 'hotfix code'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        prompt = self.mock_kimi.generate.call_args[0][0]
        assert 'api-gateway' in prompt
    
    def test_handle_alert_no_description_field(self):
        """Should use default message when description field is missing."""
        # Arrange
        alert = {'service': 'auth-service'}
        self.mock_kimi.generate.return_value = 'hotfix code'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        prompt = self.mock_kimi.generate.call_args[0][0]
        assert 'No description provided' in prompt
        assert 'auth-service' in prompt
    
    def test_handle_alert_kimi_returns_none(self):
        """Should return failure status when Kimi client returns None."""
        # Arrange
        alert = {
            'description': 'Service crashed',
            'service': 'worker-service'
        }
        self.mock_kimi.generate.return_value = None
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_failed'
        assert 'error' in result
        assert 'Blueprint generation failed' in result['error']
        assert 'blueprint' not in result
    
    def test_handle_alert_kimi_raises_exception(self):
        """Should return failure status when Kimi client raises exception."""
        # Arrange
        alert = {
            'description': 'Memory leak detected',
            'service': 'cache-service'
        }
        self.mock_kimi.generate.side_effect = Exception('API timeout')
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_failed'
        assert 'error' in result
        assert 'API timeout' in result['error']
    
    def test_handle_alert_with_additional_fields(self):
        """Should handle alert with extra fields (severity, labels, annotations)."""
        # Arrange
        alert = {
            'description': 'High CPU usage',
            'service': 'compute-engine',
            'severity': 'critical',
            'labels': {'env': 'production', 'team': 'platform'},
            'annotations': {'runbook': 'https://wiki/runbook/cpu'}
        }
        self.mock_kimi.generate.return_value = 'optimization patch'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        assert result['blueprint'] == 'optimization patch'
    
    def test_handle_alert_prompt_structure(self):
        """Should generate properly structured prompt for Kimi."""
        # Arrange
        alert = {
            'description': 'IndexError: list index out of range',
            'service': 'data-processor'
        }
        self.mock_kimi.generate.return_value = 'bounds check fix'
        
        # Act
        self.agent.handle_alert(alert)
        
        # Assert
        prompt = self.mock_kimi.generate.call_args[0][0]
        
        # Check prompt contains required sections
        assert 'CRITICAL ALERT' in prompt
        assert 'service: data-processor' in prompt
        assert 'Error Log: IndexError: list index out of range' in prompt
        assert 'Task:' in prompt
        assert 'Analyze the error' in prompt
        assert 'Generate a patch file' in prompt
        assert 'Do not refactor unrelated code' in prompt
    
    def test_handle_alert_special_characters_in_description(self):
        """Should handle alert descriptions with special characters."""
        # Arrange
        alert = {
            'description': 'Error: "User\'s input" caused <SQL> injection & failed',
            'service': 'api-service'
        }
        self.mock_kimi.generate.return_value = 'sanitization fix'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        prompt = self.mock_kimi.generate.call_args[0][0]
        assert 'User\'s input' in prompt or 'User' in prompt
    
    def test_handle_alert_very_long_description(self):
        """Should handle alerts with very long descriptions."""
        # Arrange
        long_description = 'Error occurred: ' + 'A' * 10000
        alert = {
            'description': long_description,
            'service': 'logging-service'
        }
        self.mock_kimi.generate.return_value = 'buffer fix'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
    
    def test_handle_alert_multiline_description(self):
        """Should handle multiline error descriptions."""
        # Arrange
        alert = {
            'description': '''Traceback (most recent call last):
  File "app.py", line 42, in process
    result = calculate(data)
  File "utils.py", line 15, in calculate
    return sum(values) / len(values)
ZeroDivisionError: division by zero''',
            'service': 'analytics'
        }
        self.mock_kimi.generate.return_value = 'zero division check'
        
        # Act
        result = self.agent.handle_alert(alert)
        
        # Assert
        assert result['status'] == 'hotfix_generated'
        prompt = self.mock_kimi.generate.call_args[0][0]
        assert 'ZeroDivisionError' in prompt


class TestSelfHealingAgentEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def test_concurrent_alert_handling(self):
        """Should handle multiple alerts independently."""
        mock_kimi = Mock(spec=KimiClient)
        mock_kimi.generate.side_effect = ['fix1', 'fix2', 'fix3']
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        alerts = [
            {'description': 'Error 1', 'service': 'svc1'},
            {'description': 'Error 2', 'service': 'svc2'},
            {'description': 'Error 3', 'service': 'svc3'}
        ]
        
        results = [agent.handle_alert(alert) for alert in alerts]
        
        assert all(r['status'] == 'hotfix_generated' for r in results)
        assert results[0]['blueprint'] == 'fix1'
        assert results[1]['blueprint'] == 'fix2'
        assert results[2]['blueprint'] == 'fix3'
        assert mock_kimi.generate.call_count == 3
    
    def test_handle_alert_with_none_payload(self):
        """
        Verify that calling handle_alert with a None payload raises an AttributeError.
        
        Sets up a SelfHealingAgent with a mocked KimiClient and asserts that processing a None payload results in an AttributeError.
        """
        mock_kimi = Mock(spec=KimiClient)
        mock_kimi.generate.return_value = 'fix'
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        # This will raise AttributeError when trying to call .get() on None
        with pytest.raises(AttributeError):
            agent.handle_alert(None)
    
    def test_handle_alert_with_non_dict_payload(self):
        """Should handle non-dictionary payload."""
        mock_kimi = Mock(spec=KimiClient)
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        with pytest.raises(AttributeError):
            agent.handle_alert("invalid payload")
    
    def test_handle_alert_unicode_in_description(self):
        """Should handle Unicode characters in alert description."""
        mock_kimi = Mock(spec=KimiClient)
        mock_kimi.generate.return_value = 'unicode fix'
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        alert = {
            'description': 'Error: Ünexpected chàracter in ユーザー input 中文',
            'service': 'i18n-service'
        }
        
        result = agent.handle_alert(alert)
        
        assert result['status'] == 'hotfix_generated'


class TestSelfHealingAgentIntegration:
    """Integration tests for SelfHealingAgent with real-like scenarios."""
    
    def test_realistic_database_error_scenario(self):
        """Should handle realistic database connection error."""
        mock_kimi = Mock(spec=KimiClient)
        mock_kimi.generate.return_value = '''
def fix_db_connection():
    # Add connection retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            connection = create_connection()
            return connection
        except ConnectionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
'''
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        alert = {
            'description': 'pymongo.errors.ServerSelectionTimeoutError: localhost:27017: timed out',
            'service': 'user-service',
            'severity': 'high'
        }
        
        result = agent.handle_alert(alert)
        
        assert result['status'] == 'hotfix_generated'
        assert 'retry' in result['blueprint'].lower()
    
    def test_realistic_api_timeout_scenario(self):
        """Should handle API timeout errors appropriately."""
        mock_kimi = Mock(spec=KimiClient)
        mock_kimi.generate.return_value = 'timeout handling code'
        agent = SelfHealingAgent(kimi_client=mock_kimi)
        
        alert = {
            'description': 'requests.exceptions.ReadTimeout: HTTPSConnectionPool(host="api.external.com"): Read timed out. (read timeout=5)',
            'service': 'integration-service'
        }
        
        result = agent.handle_alert(alert)
        
        assert result['status'] == 'hotfix_generated'
        
        # Verify prompt was constructed correctly
        call_args = mock_kimi.generate.call_args
        assert call_args[1]['mode'] == 'hotfix'