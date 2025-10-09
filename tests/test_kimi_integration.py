"""
Integration tests for Kimi Instruct
Tests the complete project lifecycle with the AI project manager
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kimi_instruct.core import KimiInstruct, TaskPriority, TaskStatus
from src.kimi_instruct.service import KimiService

@pytest.mark.asyncio
class TestKimiIntegration:
    """Integration tests for Kimi Instruct system"""
    
    @pytest.fixture
    async def kimi(self):
        """Create Kimi instance for testing"""
        kimi = KimiInstruct()
        return kimi
    
    @pytest.fixture
    async def kimi_service(self):
        """Create Kimi web service for testing"""
        service = KimiService()
        return service
    
    async def test_full_project_lifecycle(self, kimi):
        """Test complete project lifecycle with Kimi"""
        
        # Test 1: Create and execute a simple deployment task
        deployment_task = await kimi.create_task(
            title="Deploy monitoring stack to production",
            description="Deploy Prometheus, Grafana, and AlertManager to production environment",
            priority=TaskPriority.HIGH,
            metadata={"environment": "production", "region": "af-south-1"}
        )
        
        assert deployment_task.title == "Deploy monitoring stack to production"
        assert deployment_task.priority == TaskPriority.HIGH
        assert deployment_task.status == TaskStatus.PENDING
        
        # Execute the task
        with patch.object(kimi, 'execute_deployment', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {
                'deployment_id': 'deploy_123',
                'url': 'http://monitoring.production.local'
            }
            
            success = await kimi.execute_task(deployment_task.id)
            assert success
            assert deployment_task.status == TaskStatus.COMPLETED
    
    async def test_cost_optimization_task(self, kimi):
        """Test cost optimization functionality"""
        
        optimization_task = await kimi.create_task(
            title="Optimize monitoring costs",
            description="Analyze current costs and suggest optimizations",
            priority=TaskPriority.MEDIUM
        )
        
        # Mock the optimization execution
        with patch.object(kimi, 'handle_optimization_task', new_callable=AsyncMock) as mock_opt:
            mock_opt.return_value = {
                'savings': 2500.0,
                'optimizations': 3,
                'roi': 1.8
            }
            
            success = await kimi.execute_task(optimization_task.id)
            assert success
            
            result = optimization_task.metadata.get('result', {})
            assert 'savings' in result
            assert result['savings'] >= 0
    
    async def test_project_status_reporting(self, kimi):
        """Test project status reporting"""
        
        # Create some tasks
        await kimi.create_task(
            title="Task 1", 
            description="Test task 1", 
            priority=TaskPriority.HIGH
        )
        
        await kimi.create_task(
            title="Task 2", 
            description="Test task 2", 
            priority=TaskPriority.MEDIUM
        )
        
        # Get status report
        status = await kimi.get_status_report()
        
        assert 'project_context' in status
        assert 'task_summary' in status
        assert 'critical_issues' in status
        assert 'risk_level' in status
        assert 'next_actions' in status
        
        # Check task summary
        assert status['task_summary']['total'] == 2
        assert 'completion_percentage' in status['task_summary']
    
    async def test_human_approval_flow(self, kimi):
        """Test human approval flow for high-impact decisions"""
        
        # Create a task that should trigger human approval
        high_cost_task = await kimi.create_task(
            title="Implement multi-cloud routing",
            description="Route monitoring traffic across multiple cloud providers",
            priority=TaskPriority.HIGH,
            metadata={"budget_impact": 5000, "complexity": 9}
        )
        
        # Mock optimization to trigger approval
        with patch.object(kimi, 'handle_optimization_task', new_callable=AsyncMock) as mock_opt:
            mock_opt.return_value = await kimi.request_human_approval(
                high_cost_task,
                "High budget impact detected"
            )
            
            result = await kimi.execute_task(high_cost_task.id)
            
            # Should require human approval
            assert high_cost_task.status == TaskStatus.BLOCKED
            assert 'approval_request' in high_cost_task.metadata
    
    async def test_escalation_flow(self, kimi):
        """Test escalation flow for critical issues"""
        
        # Create a critical task
        critical_task = await kimi.create_task(
            title="Critical system check",
            description="Check critical monitoring systems",
            priority=TaskPriority.CRITICAL
        )
        
        # Mock a failure scenario
        with patch.object(kimi, 'perform_health_check', side_effect=Exception("Critical system failure")):
            success = await kimi.execute_task(critical_task.id)
            
            # Should fail and escalate
            assert not success
            assert critical_task.status == TaskStatus.BLOCKED
            assert 'error' in critical_task.metadata
            
            # Check if escalation was logged
            escalations = [d for d in kimi.decision_history if d['type'] == 'escalation']
            assert len(escalations) > 0
    
    async def test_task_dependencies(self, kimi):
        """Test task dependency management"""
        
        # Create parent task
        parent_task = await kimi.create_task(
            title="Setup infrastructure",
            description="Setup basic infrastructure",
            priority=TaskPriority.HIGH
        )
        
        # Create dependent task
        dependent_task = await kimi.create_task(
            title="Deploy application",
            description="Deploy application on infrastructure",
            priority=TaskPriority.MEDIUM,
            dependencies=[parent_task.id]
        )
        
        # Try to execute dependent task (should be blocked)
        success = await kimi.execute_task(dependent_task.id)
        assert not success
        assert dependent_task.status == TaskStatus.BLOCKED
        
        # Complete parent task
        parent_task.status = TaskStatus.COMPLETED
        
        # Now dependent task should execute
        success = await kimi.execute_task(dependent_task.id)
        assert success
    
    async def test_risk_assessment(self, kimi):
        """Test project risk assessment"""
        
        # Set high risk score
        kimi.context.metrics['risk_score'] = 0.9
        kimi.assess_project_risk()
        
        assert kimi.context.risk_level == "high"
        
        # Set low risk score
        kimi.context.metrics['risk_score'] = 0.2
        kimi.assess_project_risk()
        
        assert kimi.context.risk_level == "low"
    
    async def test_human_checkin_due(self, kimi):
        """Test human checkin timing"""
        
        # Set last checkin to long ago
        kimi.context.last_human_checkin = datetime.now() - timedelta(hours=25)
        
        assert kimi.is_human_checkin_due()
        
        # Set recent checkin
        kimi.context.last_human_checkin = datetime.now() - timedelta(hours=1)
        
        assert not kimi.is_human_checkin_due()
    
    async def test_next_actions_generation(self, kimi):
        """Test next actions recommendation"""
        
        # Create blocked critical task
        blocked_task = await kimi.create_task(
            title="Critical blocked task",
            description="This task is blocked",
            priority=TaskPriority.CRITICAL
        )
        blocked_task.status = TaskStatus.BLOCKED
        
        # Set low budget
        kimi.context.budget_remaining = 5000
        
        # Set checkin due
        kimi.context.last_human_checkin = datetime.now() - timedelta(hours=25)
        
        actions = await kimi.get_next_actions()
        
        # Should have actions for blocked task, budget, and checkin
        action_types = [action['action'] for action in actions]
        assert 'resolve_blocker' in action_types
        assert 'budget_review' in action_types
        assert 'human_checkin' in action_types
    
    async def test_web_service_endpoints(self, kimi_service):
        """Test web service HTTP endpoints"""
        from aiohttp.test_utils import make_mocked_request
        
        # Test health endpoint
        request = make_mocked_request('GET', '/health')
        response = await kimi_service.health(request)
        
        assert response.status == 200
        
        # Test status endpoint
        request = make_mocked_request('GET', '/status')
        with patch.object(kimi_service.kimi, 'get_status_report', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {
                'task_summary': {'total': 0, 'completed': 0, 'completion_percentage': 0},
                'risk_level': 'low',
                'project_context': {'budget_remaining': 50000},
                'critical_issues': [],
                'next_actions': []
            }
            
            response = await kimi_service.get_status(request)
            assert response.status == 200
    
    async def test_task_creation_via_api(self, kimi_service):
        """Test task creation via web API"""
        from aiohttp.test_utils import make_mocked_request
        import json
        
        # Mock request data
        task_data = {
            'title': 'Test API Task',
            'description': 'Task created via API',
            'priority': 'high'
        }
        
        request = make_mocked_request('POST', '/tasks', json=task_data)
        request.json = AsyncMock(return_value=task_data)
        
        response = await kimi_service.create_task(request)
        
        assert response.status == 201
        
        # Check if task was created
        assert len(kimi_service.kimi.tasks) > 0
    
    async def test_metrics_collection(self, kimi):
        """Test project metrics collection and updates"""
        
        initial_progress = kimi.context.metrics['progress']
        
        # Create and complete a high priority task
        task = await kimi.create_task(
            title="High priority task",
            description="Test task",
            priority=TaskPriority.HIGH
        )
        
        # Simulate task completion
        result = {'status': 'completed'}
        await kimi.update_project_metrics(task, result)
        
        # Progress should have increased
        assert kimi.context.metrics['progress'] > initial_progress
    
    async def test_budget_tracking(self, kimi):
        """Test budget tracking functionality"""
        
        initial_budget = kimi.context.budget_remaining
        
        # Create task with cost impact
        task = await kimi.create_task(
            title="Expensive task",
            description="Task with cost",
            priority=TaskPriority.MEDIUM
        )
        
        # Simulate task completion with cost
        result = {'cost': 1000.0}
        await kimi.update_project_metrics(task, result)
        
        # Budget should have decreased
        assert kimi.context.budget_remaining == initial_budget - 1000.0
    
    async def test_decision_history_logging(self, kimi):
        """Test decision history logging"""
        
        initial_history_count = len(kimi.decision_history)
        
        # Create task requiring approval
        task = await kimi.create_task(
            title="Approval task",
            description="Task requiring approval",
            priority=TaskPriority.HIGH,
            human_approval_required=True
        )
        
        # Request approval (should log decision)
        await kimi.request_human_approval(task, "Test approval")
        
        # Check if decision was logged
        assert len(kimi.decision_history) > initial_history_count
        
        # Check decision type
        latest_decision = kimi.decision_history[-1]
        assert latest_decision['type'] == 'approval_request'

# Additional test utilities
@pytest.fixture
def mock_prometheus_response():
    """Mock Prometheus health check response"""
    return AsyncMock(status=200, headers={'X-Response-Time': '10ms'})

@pytest.fixture
def mock_grafana_response():
    """Mock Grafana health check response"""
    return AsyncMock(status=200)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
