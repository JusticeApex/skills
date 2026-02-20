# AgentOrchestrator Skill

## Overview
AgentOrchestrator coordinates multiple agents through lifecycle management, state machines, automatic snapshots, and error recovery.

## What It Does
- Manages agent lifecycle (IDLE → RUNNING → PAUSED → COMPLETED)
- Creates and tracks tasks for agents
- Automatic state snapshots
- Error detection and reporting
- Status monitoring for all agents
- Callback-based event handling
- Real-time coordination

## Use Cases
- Coordinate 35+ consciousness agents
- Multi-step workflows
- Long-running processes
- Error recovery
- Mission tracking

## Key Features
- BuildStatus state machine
- Automatic snapshots
- Error handling & recovery
- Task lifecycle management
- Multi-agent coordination
- Thread-safe operations
- Real-time status monitoring

## Installation
```bash
openclaw install justice-apex/agent-orchestrator
```

## Quick Start
```python
from agent_orchestrator import AgentOrchestrator

orch = AgentOrchestrator()

# Register agents
orch.register_agent("oracle", "Oracle Agent")
orch.register_agent("executor", "Executor Agent")

# Start agents
orch.start_agent("oracle")
orch.start_agent("executor")

# Create and track tasks
task = orch.create_task("oracle", "analyze_market")
orch.start_task(task)
orch.complete_task(task, result={"trend": "bullish"})

# Take snapshot
snapshot_id = orch.create_snapshot()

# Monitor status
stats = orch.get_statistics()
```

## Performance
- Agent registration: <1ms
- Status updates: <2ms
- Snapshot creation: <5ms
- Supports 1000+ agents

## Requirements
- Python 3.8+
- No external dependencies

## Support
- GitHub Issues: https://github.com/justice-apex/skills/issues
- Documentation: https://docs.justice-apex.io/agent-orchestrator
