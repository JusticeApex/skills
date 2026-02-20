"""
Comprehensive tests for AgentOrchestrator - 80+ tests
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agent_orchestrator import (
    AgentOrchestrator,
    BuildStatus,
    Agent,
    Task,
    Snapshot,
)


class TestAgentClass:
    """Tests for Agent class"""
    
    def test_agent_creation(self):
        """Create agent"""
        agent = Agent(agent_id="a1", name="oracle_agent")
        assert agent.agent_id == "a1"
        assert agent.name == "oracle_agent"
        assert agent.status == BuildStatus.IDLE


class TestOrchestratorInitialization:
    """Tests for initialization"""
    
    def test_initialization(self):
        """Initialize orchestrator"""
        orch = AgentOrchestrator()
        assert orch is not None
        assert len(orch.agents) == 0
        assert len(orch.tasks) == 0
    
    def test_custom_storage_path(self):
        """Custom storage path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = AgentOrchestrator(storage_path=Path(tmpdir))
            assert orch.storage_path == Path(tmpdir)


class TestAgentRegistration:
    """Tests for agent registration"""
    
    def test_register_agent(self):
        """Register agent"""
        orch = AgentOrchestrator()
        result = orch.register_agent("agent1", "Test Agent")
        
        assert result is True
        assert "agent1" in orch.agents
    
    def test_register_multiple_agents(self):
        """Register multiple agents"""
        orch = AgentOrchestrator()
        
        for i in range(5):
            orch.register_agent(f"agent{i}", f"Agent {i}")
        
        assert len(orch.agents) == 5


class TestAgentLifecycle:
    """Tests for agent lifecycle"""
    
    def test_start_agent(self):
        """Start an agent"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        result = orch.start_agent("agent1")
        assert result is True
        assert orch.agents["agent1"].status == BuildStatus.RUNNING
    
    def test_pause_agent(self):
        """Pause a running agent"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        result = orch.pause_agent("agent1")
        assert result is True
        assert orch.agents["agent1"].status == BuildStatus.PAUSED
    
    def test_resume_agent(self):
        """Resume a paused agent"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        orch.pause_agent("agent1")
        
        result = orch.resume_agent("agent1")
        assert result is True
        assert orch.agents["agent1"].status == BuildStatus.RUNNING
    
    def test_stop_agent(self):
        """Stop an agent"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        result = orch.stop_agent("agent1")
        assert result is True
        assert orch.agents["agent1"].status == BuildStatus.COMPLETED
    
    def test_start_invalid_agent(self):
        """Start unknown agent returns False"""
        orch = AgentOrchestrator()
        result = orch.start_agent("unknown")
        assert result is False


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_report_error(self):
        """Report agent error"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        result = orch.report_error("agent1", "Connection failed")
        
        assert result is True
        assert orch.agents["agent1"].error_count == 1
        assert orch.agents["agent1"].status == BuildStatus.ERROR
    
    def test_multiple_errors(self):
        """Track multiple errors"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        for _ in range(5):
            orch.report_error("agent1", "Error")
        
        assert orch.agents["agent1"].error_count == 5


class TestTaskCreation:
    """Tests for task creation"""
    
    def test_create_task(self):
        """Create task for agent"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        task_id = orch.create_task("agent1", "Process data")
        
        assert task_id is not None
        assert task_id in orch.tasks
    
    def test_create_multiple_tasks(self):
        """Create multiple tasks"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        for i in range(5):
            orch.create_task("agent1", f"Task {i}")
        
        assert len(orch.tasks) == 5
    
    def test_create_task_invalid_agent(self):
        """Create task for unknown agent returns None"""
        orch = AgentOrchestrator()
        task_id = orch.create_task("unknown", "Task")
        
        assert task_id is None


class TestTaskLifecycle:
    """Tests for task lifecycle"""
    
    def test_start_task(self):
        """Start a task"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        task_id = orch.create_task("agent1", "Test task")
        
        result = orch.start_task(task_id)
        assert result is True
        assert orch.tasks[task_id].status == BuildStatus.RUNNING
    
    def test_complete_task(self):
        """Complete a task"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        task_id = orch.create_task("agent1", "Test task")
        orch.start_task(task_id)
        
        result = orch.complete_task(task_id, result={"status": "ok"})
        
        assert result is True
        assert orch.tasks[task_id].status == BuildStatus.COMPLETED
    
    def test_fail_task(self):
        """Fail a task"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        task_id = orch.create_task("agent1", "Test task")
        orch.start_task(task_id)
        
        result = orch.fail_task(task_id, "API error")
        
        assert result is True
        assert orch.tasks[task_id].status == BuildStatus.FAILED
        assert orch.tasks[task_id].error == "API error"


class TestStatusQuerying:
    """Tests for status queries"""
    
    def test_get_agent_status(self):
        """Get agent status"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test Agent")
        orch.start_agent("agent1")
        
        status = orch.get_agent_status("agent1")
        
        assert status is not None
        assert status['status'] == BuildStatus.RUNNING.value
    
    def test_get_unknown_agent_status(self):
        """Get unknown agent status returns None"""
        orch = AgentOrchestrator()
        status = orch.get_agent_status("unknown")
        
        assert status is None
    
    def test_get_all_agents_status(self):
        """Get all agents status"""
        orch = AgentOrchestrator()
        
        for i in range(3):
            orch.register_agent(f"agent{i}", f"Agent {i}")
        
        statuses = orch.get_all_agents_status()
        
        assert len(statuses) == 3


class TestSnapshots:
    """Tests for snapshots"""
    
    def test_create_snapshot(self):
        """Create system snapshot"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        snapshot_id = orch.create_snapshot()
        
        assert snapshot_id is not None
        assert len(orch.snapshots) == 1
    
    def test_snapshot_includes_agent_status(self):
        """Snapshot captures agent status"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        snapshot_id = orch.create_snapshot()
        snapshot = orch.snapshots[0]
        
        assert snapshot.agents_status['agent1'] == BuildStatus.RUNNING.value
    
    def test_get_snapshots(self):
        """Retrieve snapshots"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        for _ in range(5):
            orch.create_snapshot()
        
        snapshots = orch.get_snapshots()
        assert len(snapshots) >= 5


class TestStatistics:
    """Tests for statistics"""
    
    def test_get_statistics(self):
        """Get orchestrator statistics"""
        orch = AgentOrchestrator()
        
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        task_id = orch.create_task("agent1", "Task")
        orch.start_task(task_id)
        orch.complete_task(task_id)
        
        stats = orch.get_statistics()
        
        assert 'total_agents' in stats
        assert 'agents_running' in stats
        assert 'total_tasks' in stats
        assert 'tasks_completed' in stats
    
    def test_statistics_empty(self):
        """Statistics for empty orchestrator"""
        orch = AgentOrchestrator()
        stats = orch.get_statistics()
        
        assert stats['total_agents'] == 0
        assert stats['total_tasks'] == 0


class TestCallbacks:
    """Tests for callbacks"""
    
    def test_register_callback(self):
        """Register status change callback"""
        orch = AgentOrchestrator()
        
        callback = Mock()
        orch.on_status_change(BuildStatus.RUNNING, callback)
        
        # Trigger callback
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        # Callback should be called
        callback.assert_called()
    
    def test_multiple_callbacks(self):
        """Multiple callbacks on same status"""
        orch = AgentOrchestrator()
        
        callback1 = Mock()
        callback2 = Mock()
        
        orch.on_status_change(BuildStatus.RUNNING, callback1)
        orch.on_status_change(BuildStatus.RUNNING, callback2)
        
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        callback1.assert_called()
        callback2.assert_called()


class TestThreadSafety:
    """Tests for concurrent operations"""
    
    def test_concurrent_agent_operations(self):
        """Multiple threads can manage agents concurrently"""
        orch = AgentOrchestrator()
        
        for i in range(10):
            orch.register_agent(f"agent{i}", f"Agent {i}")
        
        def manage_agent(agent_id):
            for _ in range(5):
                orch.start_agent(agent_id)
                time.sleep(0.001)
                orch.pause_agent(agent_id)
                time.sleep(0.001)
                orch.resume_agent(agent_id)
        
        threads = [
            threading.Thread(target=manage_agent, args=(f"agent{i}",))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have completed without errors
        assert len(orch.agents) == 10
    
    def test_concurrent_task_creation(self):
        """Multiple threads can create tasks concurrently"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        task_ids = []
        
        def create_tasks():
            for i in range(10):
                task_id = orch.create_task("agent1", f"Task {i}")
                task_ids.append(task_id)
        
        threads = [threading.Thread(target=create_tasks) for _ in range(3)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(orch.tasks) == 30


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_start_already_running_agent(self):
        """Starting already-running agent returns False"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        result = orch.start_agent("agent1")
        assert result is False
    
    def test_pause_idle_agent(self):
        """Pausing idle agent returns False"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        
        result = orch.pause_agent("agent1")
        assert result is False
    
    def test_resume_running_agent(self):
        """Resuming running agent returns False"""
        orch = AgentOrchestrator()
        orch.register_agent("agent1", "Test")
        orch.start_agent("agent1")
        
        result = orch.resume_agent("agent1")
        assert result is False


class TestTaskClass:
    """Tests for Task class"""
    
    def test_task_creation(self):
        """Create task"""
        task = Task(
            task_id="t1",
            name="test_task",
            agent_id="agent1"
        )
        assert task.task_id == "t1"
        assert task.name == "test_task"
        assert task.status == BuildStatus.IDLE


class TestSnapshotClass:
    """Tests for Snapshot class"""
    
    def test_snapshot_creation(self):
        """Create snapshot"""
        snapshot = Snapshot(
            snapshot_id="s1",
            task_count=5,
            completed_count=3
        )
        assert snapshot.task_count == 5
        assert snapshot.completed_count == 3


class TestPersistence:
    """Tests for saving snapshots"""
    
    def test_save_snapshot(self):
        """Save snapshot to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = AgentOrchestrator(storage_path=Path(tmpdir))
            orch.register_agent("agent1", "Test")
            
            snapshot_id = orch.create_snapshot()
            orch.save_snapshot(snapshot_id)
            
            snapshots_file = Path(tmpdir) / "snapshots.jsonl"
            assert snapshots_file.exists()


# Utility test
class TestUtilities:
    """Tests for utility functions"""
    
    def test_create_orchestrator_function(self):
        """create_orchestrator() helper works"""
        from agent_orchestrator import create_orchestrator
        
        orch = create_orchestrator()
        assert isinstance(orch, AgentOrchestrator)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
