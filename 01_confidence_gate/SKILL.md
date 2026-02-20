# ConfidenceGate Skill

## Overview
ConfidenceGate is a quality control system that evaluates every action before execution, enabling safe automation by distinguishing between high-confidence actions (execute immediately) and risky operations (pause for review).

## What It Does
- Evaluates action safety across 4 confidence levels
- Auto-executes safe actions (HIGH confidence)
- Logs and executes medium-risk actions (MEDIUM confidence)
- Pauses and waits for human approval (LOW confidence)
- Always pauses critical/dangerous operations (CRITICAL confidence)
- Adjusts confidence dynamically based on context and risk factors

## Use Cases
- Autonomous trading systems (pause large trades, auto-execute small ones)
- Code deployment (auto-deploy test updates, pause production)
- Financial operations (auto-process small payments, review large transfers)
- Infrastructure changes (pause before critical changes, auto-apply safe updates)
- Healthcare systems (pause decisions affecting patient safety, auto-execute routine checks)

## Key Features
- 4 confidence levels with custom thresholds
- Risk factor adjustments (market volatility, error rates, etc.)
- Complete decision history and audit trail
- Custom rules per action type
- Manual override capability
- Transparent scoring explanation

## Installation
```bash
openclaw install justice-apex/confidence-gate
```

## Quick Start
```python
from confidence_gate import ConfidenceGate, ActionConfidence

gate = ConfidenceGate()

# Register action types with confidence levels
gate.register_action('make_trade', ActionConfidence.MEDIUM)
gate.register_action('deploy_code', ActionConfidence.MEDIUM)
gate.register_action('delete_file', ActionConfidence.CRITICAL)

# Evaluate action
result = gate.evaluate_action(
    action='make_trade',
    amount=100,
    risk_factors={'volatility': 0.65}
)

if result.should_execute:
    print(f"Execute: {result.action}")
else:
    print(f"Paused for review: {result.action}")
    # Wait for human approval
    if await_approval():
        gate.force_execute(result)
```

## Performance
- Evaluation latency: <5ms
- Memory per action: ~1KB
- Scales to 100,000+ actions without degradation

## Requirements
- Python 3.8+
- Dependencies: dataclasses, enum, threading

## Support
- GitHub Issues: https://github.com/justice-apex/skills/issues
- Documentation: https://docs.justice-apex.io/confidence-gate
- Examples: https://github.com/justice-apex/skills/tree/main/skills/01_confidence_gate/examples
