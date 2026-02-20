"""
AGENT ORCHESTRATOR - Multi-Agent Lifecycle Management
======================================================

Coordinates multiple agents through lifecycle management, state machines,
automatic snapshots, and error recovery.

Features:
- BuildStatus state machine (IDLE→RUNNING→PAUSED→COMPLETED)
- Automatic state snapshots
- Error handling & recovery
- Task lifecycle callbacks
- Multi-agent coordination
- Real-time status monitoring

Author: Justice Apex LLC
License: MIT
"""

import threading
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class Agent:
    """An agent in the system"""
    agent_id: str
    name: str
    status: BuildStatus = BuildStatus.IDLE
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    error_count: int = 0
    task_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Task:
    """A task for agents to execute"""
    task_id: str
    name: str
    agent_id: str
    status: BuildStatus = BuildStatus.IDLE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Snapshot:
    """System state snapshot"""
    snapshot_id: str
    timestamp: str
    agents_status: Dict[str, str] = field(default_factory=dict)
    task_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AgentOrchestrator:
    """
    Multi-agent lifecycle management system.
    
    Coordinates agents through state machine, tracks status,
    creates snapshots, and handles errors.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize orchestrator
        
        Args:
            storage_path: Path for storing snapshots and logs
        """
        self.storage_path = storage_path or Path("agent_orchestrator_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Registered agents
        self.agents: Dict[str, Agent] = {}
        
        # Tasks
        self.tasks: Dict[str, Task] = {}
        
        # Snapshots
        self.snapshots: deque = deque(maxlen=1000)
        
        # Callbacks
        self.callbacks: Dict[BuildStatus, List[Callable]] = defaultdict(list)
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info("AgentOrchestrator initialized")
    
    def register_agent(self, agent_id: str, name: str) -> bool:
        """
        Register an agent
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
        
        Returns:
            True if registered
        """
        with self._lock:
            agent = Agent(agent_id=agent_id, name=name)
            self.agents[agent_id] = agent
            
            logger.info(f"Agent registered: {name} ({agent_id})")
            return True
    
    def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent
        
        Args:
            agent_id: Agent to start
        
        Returns:
            True if started
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            if agent.status == BuildStatus.IDLE:
                agent.status = BuildStatus.RUNNING
                agent.last_heartbeat = datetime.now().isoformat()
                
                self._trigger_callbacks(BuildStatus.RUNNING)
                logger.info(f"Agent started: {agent.name}")
                return True
            
            return False
    
    def pause_agent(self, agent_id: str) -> bool:
        """
        Pause an agent
        
        Args:
            agent_id: Agent to pause
        
        Returns:
            True if paused
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            if agent.status == BuildStatus.RUNNING:
                agent.status = BuildStatus.PAUSED
                
                self._trigger_callbacks(BuildStatus.PAUSED)
                logger.info(f"Agent paused: {agent.name}")
                return True
            
            return False
    
    def resume_agent(self, agent_id: str) -> bool:
        """
        Resume a paused agent
        
        Args:
            agent_id: Agent to resume
        
        Returns:
            True if resumed
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            if agent.status == BuildStatus.PAUSED:
                agent.status = BuildStatus.RUNNING
                agent.last_heartbeat = datetime.now().isoformat()
                
                logger.info(f"Agent resumed: {agent.name}")
                return True
            
            return False
    
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent
        
        Args:
            agent_id: Agent to stop
        
        Returns:
            True if stopped
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            agent.status = BuildStatus.COMPLETED
            
            self._trigger_callbacks(BuildStatus.COMPLETED)
            logger.info(f"Agent stopped: {agent.name}")
            return True
    
    def report_error(self, agent_id: str, error: str) -> bool:
        """
        Report error for an agent
        
        Args:
            agent_id: Agent with error
            error: Error description
        
        Returns:
            True if reported
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            agent.error_count += 1
            agent.status = BuildStatus.ERROR
            
            logger.error(f"Agent error: {agent.name} - {error}")
            return True
    
    def create_task(
        self,
        agent_id: str,
        task_name: str
    ) -> Optional[str]:
        """
        Create task for agent
        
        Args:
            agent_id: Agent to assign task
            task_name: Task name
        
        Returns:
            Task ID, or None
        """
        with self._lock:
            if agent_id not in self.agents:
                return None
            
            task_id = self._generate_id()
            task = Task(
                task_id=task_id,
                name=task_name,
                agent_id=agent_id
            )
            
            self.tasks[task_id] = task
            self.agents[agent_id].task_count += 1
            
            logger.info(f"Task created: {task_name} (ID: {task_id})")
            return task_id
    
    def start_task(self, task_id: str) -> bool:
        """
        Start a task
        
        Args:
            task_id: Task to start
        
        Returns:
            True if started
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            if task.status == BuildStatus.IDLE:
                task.status = BuildStatus.RUNNING
                task.started_at = datetime.now().isoformat()
                
                logger.info(f"Task started: {task.name}")
                return True
            
            return False
    
    def complete_task(self, task_id: str, result: Optional[Any] = None) -> bool:
        """
        Mark task as completed
        
        Args:
            task_id: Task to complete
            result: Task result
        
        Returns:
            True if completed
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = BuildStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.result = result
            
            logger.info(f"Task completed: {task.name}")
            return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Mark task as failed
        
        Args:
            task_id: Task that failed
            error: Error description
        
        Returns:
            True if marked as failed
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = BuildStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            task.error = error
            
            logger.error(f"Task failed: {task.name} - {error}")
            return True
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent status
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Agent status dict
        """
        with self._lock:
            if agent_id not in self.agents:
                return None
            
            agent = self.agents[agent_id]
            return {
                'agent_id': agent.agent_id,
                'name': agent.name,
                'status': agent.status.value,
                'error_count': agent.error_count,
                'task_count': agent.task_count
            }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all agents
        
        Returns:
            Dict of agent statuses
        """
        with self._lock:
            return {
                agent_id: {
                    'name': agent.name,
                    'status': agent.status.value,
                    'error_count': agent.error_count,
                    'task_count': agent.task_count
                }
                for agent_id, agent in self.agents.items()
            }
    
    def create_snapshot(self) -> str:
        """
        Create system state snapshot
        
        Returns:
            Snapshot ID
        """
        with self._lock:
            snapshot_id = self._generate_id()
            
            agents_status = {
                agent_id: agent.status.value
                for agent_id, agent in self.agents.items()
            }
            
            completed = sum(1 for t in self.tasks.values() if t.status == BuildStatus.COMPLETED)
            failed = sum(1 for t in self.tasks.values() if t.status == BuildStatus.FAILED)
            
            snapshot = Snapshot(
                snapshot_id=snapshot_id,
                agents_status=agents_status,
                task_count=len(self.tasks),
                completed_count=completed,
                failed_count=failed
            )
            
            self.snapshots.appendleft(snapshot)
            
            logger.info(f"Snapshot created: {snapshot_id}")
            return snapshot_id
    
    def get_snapshots(self, limit: int = 50) -> List[Snapshot]:
        """
        Get snapshots
        
        Args:
            limit: Maximum snapshots
        
        Returns:
            List of snapshots
        """
        with self._lock:
            return list(self.snapshots)[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics
        
        Returns:
            Statistics dict
        """
        with self._lock:
            tasks_completed = sum(1 for t in self.tasks.values() if t.status == BuildStatus.COMPLETED)
            tasks_failed = sum(1 for t in self.tasks.values() if t.status == BuildStatus.FAILED)
            tasks_running = sum(1 for t in self.tasks.values() if t.status == BuildStatus.RUNNING)
            
            agents_running = sum(1 for a in self.agents.values() if a.status == BuildStatus.RUNNING)
            agents_errors = sum(a.error_count for a in self.agents.values())
            
            return {
                'total_agents': len(self.agents),
                'agents_running': agents_running,
                'agent_errors': agents_errors,
                'total_tasks': len(self.tasks),
                'tasks_completed': tasks_completed,
                'tasks_failed': tasks_failed,
                'tasks_running': tasks_running,
                'total_snapshots': len(self.snapshots)
            }
    
    def on_status_change(
        self,
        status: BuildStatus,
        callback: Callable
    ) -> None:
        """
        Register callback for status change
        
        Args:
            status: Status to trigger on
            callback: Callback function
        """
        with self._lock:
            self.callbacks[status].append(callback)
    
    def save_snapshot(self, snapshot_id: str):
        """Save snapshot to disk"""
        snapshots_file = self.storage_path / "snapshots.jsonl"
        
        with self._lock:
            try:
                with open(snapshots_file, 'a') as f:
                    for snapshot in self.snapshots:
                        if snapshot.snapshot_id == snapshot_id:
                            f.write(json.dumps(snapshot.to_dict()) + '\n')
                            break
                
                logger.info(f"Snapshot saved: {snapshot_id}")
            
            except Exception as e:
                logger.error(f"Failed to save snapshot: {e}")
    
    # Private methods
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        timestamp = datetime.now().isoformat()
        data = f"{timestamp}_{len(self.agents)}".encode()
        return hashlib.md5(data).hexdigest()[:12]
    
    def _trigger_callbacks(self, status: BuildStatus):
        """Trigger callbacks for status"""
        for callback in self.callbacks[status]:
            try:
                callback()
            except Exception as e:
                logger.error(f"Callback error: {e}")


def create_orchestrator() -> AgentOrchestrator:
    """Create and return AgentOrchestrator instance"""
    return AgentOrchestrator()
