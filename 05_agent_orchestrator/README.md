# AgentOrchestrator - Multi-Agent Lifecycle Management

Coordinates multiple agents through their entire lifecycle with state machines, automatic snapshots, and error recovery.

## Key Benefits

- **Lifecycle Management**: IDLE → RUNNING → PAUSED → COMPLETED state machine
- **Task Tracking**: Create and monitor tasks for each agent
- **Automatic Snapshots**: Captures system state at critical moments
- **Error Recovery**: Automatic detection and handling of agent failures
- **Real-Time Monitoring**: Get instant status of all agents
- **Thread-Safe**: Safely coordinate 1000+ agents concurrently

## Installation

```bash
pip install justice-apex-agent-orchestrator
```

## Quick Start

```python
from agent_orchestrator import AgentOrchestrator

# Create orchestrator
orch = AgentOrchestrator()

# Register agents
orch.register_agent("oracle_agent", "Market Oracle")
orch.register_agent("executor_agent", "Trade Executor")

# Start agents
orch.start_agent("oracle_agent")
orch.start_agent("executor_agent")

# Create tasks
analyze_task = orch.create_task("oracle_agent", "analyze_market")
orch.start_task(analyze_task)
orch.complete_task(analyze_task, result={"trend": "bullish"})

# Monitor status
stats = orch.get_statistics()
print(f"Agents running: {stats['agents_running']}")
print(f"Tasks completed: {stats['tasks_completed']}")
```

## State Machine

```
┌─────────────────────────────────────────────┐
│              AGENT LIFECYCLE                │
├─────────────────────────────────────────────┤
│                                             │
│  IDLE ──start──> RUNNING ──pause──> PAUSED │
│                    │       │                │
│                    │   error  ──> ERROR     │
│                    │       │         │      │
│                    └──stop─┴─────────┘      │
│                          │                  │
│                       COMPLETED             │
│                                             │
└─────────────────────────────────────────────┘
```

## Complete Example: Multi-Agent Trading System

```python
from agent_orchestrator import AgentOrchestrator

class TradingOrchestration:
    def __init__(self):
        self.orch = AgentOrchestrator()
        self._setup_agents()
    
    def _setup_agents(self):
        # Register 3 specialized agents
        self.orch.register_agent("market_oracle", "Market Analysis Agent")
        self.orch.register_agent("risk_manager", "Risk Management Agent")
        self.orch.register_agent("executor", "Trade Execution Agent")
        
        # Register callbacks
        self.orch.on_status_change(BuildStatus.ERROR, self._handle_error)
        self.orch.on_status_change(BuildStatus.COMPLETED, self._handle_completion)
    
    def run_trading_cycle(self):
        # Start all agents
        self.orch.start_agent("market_oracle")
        self.orch.start_agent("risk_manager")
        self.orch.start_agent("executor")
        
        # Create tasks
        analysis = self.orch.create_task("market_oracle", "analyze_market")
        self.orch.start_task(analysis)
        
        # Simulate analysis
        market_data = analyze_market()
        self.orch.complete_task(analysis, result=market_data)
        
        # Risk assessment
        risk_task = self.orch.create_task("risk_manager", "assess_risk")
        self.orch.start_task(risk_task)
        risk_level = assess_risk(market_data)
        self.orch.complete_task(risk_task, result=risk_level)
        
        # Execute if risk acceptable
        if risk_level < 0.3:
            exec_task = self.orch.create_task("executor", "execute_trade")
            self.orch.start_task(exec_task)
            result = execute_trade()
            self.orch.complete_task(exec_task, result=result)
        
        # Create snapshot for audit trail
        snapshot_id = self.orch.create_snapshot()
        
        return snapshot_id
    
    def _handle_error(self):
        """Callback when agent errors"""
        stats = self.orch.get_statistics()
        if stats['agent_errors'] > 5:
            # Escalate if too many errors
            self._escalate_alert()
    
    def _handle_completion(self):
        """Callback when agent completes"""
        stats = self.orch.get_statistics()
        print(f"Progress: {stats['tasks_completed']}/{stats['total_tasks']} tasks")
```

## Monitoring & Snapshots

```python
# Get real-time status
status = orch.get_all_agents_status()
for agent_id, status in status.items():
    print(f"{agent_id}: {status['status']} ({status['error_count']} errors)")

# Take snapshot at critical moments
snapshot_id = orch.create_snapshot()

# Review snapshots
snapshots = orch.get_snapshots(limit=10)
for snapshot in snapshots:
    print(f"Snapshot {snapshot.snapshot_id}:")
    print(f"  Agents: {snapshot.agents_status}")
    print(f"  Tasks: {snapshot.task_count}")
    print(f"  Completed: {snapshot.completed_count}")
```

## Error Handling

```python
# Report errors automatically
try:
    result = agent.execute_task()
except Exception as e:
    orch.report_error("executor", str(e))
    
    # Pause and recover
    orch.pause_agent("executor")
    recover_state()
    orch.resume_agent("executor")
```

## Performance

- Agent registration: <1ms
- Status updates: <2ms
- Snapshot creation: <5ms
- Supports 1000+ concurrent agents

## Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Testing

```bash
pytest tests/test_agent_orchestrator.py -v
```

## License

MIT - Open source and free for commercial use
