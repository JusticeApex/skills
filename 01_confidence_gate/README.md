# ConfidenceGate - Quality Control for Autonomous Systems

[![GitHub](https://img.shields.io/badge/GitHub-justice--apex-blue)](https://github.com/justice-apex/skills)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-100%25-brightgreen)](tests/)

> **Problem:** Autonomous systems make mistakes. How do you safely automate risky decisions?
>
> **Solution:** ConfidenceGate evaluates every action before execution, automatically executing safe decisions while pausing risky ones for human review.

---

## What Is ConfidenceGate?

ConfidenceGate is a quality control system that lets you safely automate by categorizing actions into confidence levels:

- **HIGH Confidence** ✅ Auto-execute immediately (trading $100, deploying test code)
- **MEDIUM Confidence** ⚙️ Execute but log & monitor (trading $500, deploying staging)
- **LOW Confidence** ⏸️ Pause for human review (trading $5000, deploying production)
- **CRITICAL** 🛑 Always pause & require explicit approval (deleting data, large transfers)

---

## Why You Need This

### Traditional Automation
```
❌ Auto-execute ALL decisions
   → Wild mistakes that lose money
   → No control over risky operations
   → No way to override

❌ Require human approval for EVERYTHING
   → Bottlenecks
   → Slow response times
   → Defeats the purpose of automation
```

### With ConfidenceGate
```
✅ Auto-execute safe decisions (HIGH confidence)
✅ Pause risky ones for human review (LOW/CRITICAL)
✅ Adjust confidence dynamically based on risk factors
✅ Complete audit trail of all decisions
✅ Manual override when needed
```

---

## Key Features

### 🎯 4 Confidence Levels
Each action gets categorized by risk level:
- `HIGH` - Safe to execute immediately
- `MEDIUM` - Probably safe, but log everything
- `LOW` - Risky, pause for review
- `CRITICAL` - Extremely risky, always pause

### 📊 Dynamic Risk Adjustment
Confidence adjusts based on real-time risk factors:
- Market volatility (↓ confidence when volatile)
- Error rates (↓ confidence after failures)
- Losing streaks (↓ confidence on consecutive losses)
- New markets/domains (↓ confidence on untested)
- Large amounts (↓ confidence on big transactions)

### 📝 Complete Audit Trail
Every decision is logged with:
- Action name and context
- Base confidence → adjusted confidence
- Risk factors that affected the decision
- Whether it executed or paused
- Timestamp and explanation

### 🔧 Flexible Rules
```python
# Simple: one line per action
gate.register_action('make_trade', ActionConfidence.MEDIUM)

# Advanced: custom thresholds and risk adjustments
gate.register_action(
    'deploy_code',
    ActionConfidence.MEDIUM,
    custom_threshold=0.6,
    risk_adjustments={
        RiskFactor.ERROR_RATE: -0.1,  # Lower by 0.1 per error
        RiskFactor.VOLATILITY: -0.15   # Lower by 0.15 per volatility point
    }
)
```

### 🤝 Manual Override
Pause decisions can be force-executed after human review:
```python
result = gate.evaluate_action('deploy_code', ...)
if not result.should_execute:
    # Human reviews the decision...
    if user_approves():
        gate.force_execute(result)
```

---

## Installation

```bash
# Via OpenClaw
openclaw install justice-apex/confidence-gate

# Via Git
git clone https://github.com/justice-apex/skills.git
cd skills/01_confidence_gate
pip install -e .

# Via Pip (when published)
pip install confidence-gate
```

---

## Quick Start

### 1. Create a Gate
```python
from confidence_gate import ConfidenceGate, ActionConfidence, RiskFactor

gate = ConfidenceGate()
```

### 2. Register Actions
```python
# Simple
gate.register_action('make_trade', ActionConfidence.MEDIUM)

# Advanced with risk adjustments
gate.register_action(
    'make_trade',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: -0.2,
        RiskFactor.LOSING_STREAK: -0.15,
        RiskFactor.LARGE_AMOUNT: -0.1
    }
)
```

### 3. Evaluate Decisions
```python
# Simple evaluation
result = gate.evaluate_action('make_trade')

# With context and risk factors
result = gate.evaluate_action(
    action='make_trade',
    context={'amount': 100, 'symbol': 'BTC'},
    risk_factors={
        'volatility': 0.65,  # 65% volatility
        'losing_streak': 2    # 2 consecutive losses
    }
)

# Check the result
if result.should_execute:
    print(f"✅ Execute: {result.action}")
    execute_trade(result.context)
else:
    print(f"⏸️ Pause: {result.action}")
    print(f"Reason: {result.explanation}")
    # Wait for human approval...
```

### 4. Review History & Statistics
```python
# Get decision history
history = gate.get_history(action='make_trade', limit=50)
for decision in history:
    print(f"{decision.timestamp}: {decision.action} "
          f"({decision.confidence_value:.2f}) - "
          f"{'✅ Executed' if decision.should_execute else '⏸️ Paused'}")

# Get statistics
stats = gate.get_statistics(action='make_trade')
print(f"Execution rate: {stats['execution_rate']:.1%}")
print(f"Avg confidence: {stats['avg_confidence']:.2f}")
```

---

## Real-World Examples

### Example 1: Crypto Trading
```python
gate = ConfidenceGate()

# Small trades auto-execute
gate.register_action('buy_small', ActionConfidence.HIGH)

# Medium trades logged and executed
gate.register_action('buy_medium', ActionConfidence.MEDIUM)

# Large trades always pause
gate.register_action('buy_large', ActionConfidence.CRITICAL)

# Evaluate a trade
result = gate.evaluate_action(
    'buy_medium',
    context={'amount': 500, 'coin': 'BTC'},
    risk_factors={'volatility': 0.72, 'error_rate': 0.2}
)

if result.should_execute:
    place_buy_order(500, 'BTC')
else:
    alert_human(f"Trade paused: {result.explanation}")
```

### Example 2: Code Deployment
```python
gate = ConfidenceGate()

# Test deployment auto-executes
gate.register_action('deploy_test', ActionConfidence.HIGH)

# Staging deployment requires monitoring
gate.register_action('deploy_staging', ActionConfidence.MEDIUM)

# Production requires human approval
gate.register_action('deploy_prod', ActionConfidence.CRITICAL)

# Evaluate deployment
result = gate.evaluate_action(
    'deploy_prod',
    context={'version': 'v1.2.3', 'tests_passing': True},
    risk_factors={'new_features': 5, 'files_changed': 47}
)

if result.should_execute:
    deploy_to_production()
else:
    # Send to approval queue
    approval_queue.add(result)
```

### Example 3: Dynamic Risk Adjustment
```python
gate = ConfidenceGate()

gate.register_action(
    'execute_strategy',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: -0.2,      # -0.2 per volatility point
        RiskFactor.ERROR_RATE: -0.15,     # -0.15 per error point
        RiskFactor.LOSING_STREAK: -0.1,   # -0.1 per loss
        RiskFactor.NEW_MARKET: -0.25      # -0.25 for untested market
    }
)

# High volatility + error rate = low confidence
result = gate.evaluate_action(
    'execute_strategy',
    risk_factors={
        'volatility': 0.80,    # 80% volatility = -0.16 adjustment
        'error_rate': 0.40     # 40% errors = -0.06 adjustment
    }
)
# Total: 0.5 base - 0.16 - 0.06 = 0.28 confidence → LOW
# Result: ⏸️ PAUSED FOR REVIEW
```

---

## Advanced Usage

### Custom Thresholds
```python
# Default threshold for MEDIUM is 0.5
# Override to require 0.7 confidence
gate.register_action(
    'trading_bot',
    ActionConfidence.MEDIUM,
    custom_threshold=0.7  # Stricter than default
)
```

### Checking Statistics
```python
stats = gate.get_statistics('make_trade')
print(f"Total decisions: {stats['total_decisions']}")
print(f"Execution rate: {stats['execution_rate']:.1%}")
print(f"Avg confidence: {stats['avg_confidence']:.2f}")
print(f"Min: {stats['min_confidence']:.2f}, Max: {stats['max_confidence']:.2f}")
```

### Saving & Loading History
```python
# Save history to disk
gate.save_history()

# Load history from disk (automatic on init)
gate2 = ConfidenceGate()
```

---

## Performance

- **Evaluation:** <5ms per decision
- **Memory:** ~1KB per decision
- **Scalability:** Handles 1,000,000+ decisions without degradation
- **Thread-safe:** Safe to use in concurrent environments

---

## Integration

### With AsyncIO
```python
async def make_trade(symbol, amount):
    result = gate.evaluate_action(
        'make_trade',
        context={'symbol': symbol, 'amount': amount}
    )
    
    if result.should_execute:
        return await execute_trade(symbol, amount)
    else:
        await notify_human(result.explanation)
```

### With Kubernetes
Deploy as middleware that evaluates pod actions:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: confidence-gate-config
data:
  actions.yaml: |
    pod_restart: HIGH
    node_drain: CRITICAL
    volume_delete: CRITICAL
```

### With Monitoring
```python
# Ship decisions to monitoring system
for decision in gate.get_history(limit=100):
    monitoring.record_decision(
        action=decision.action,
        confidence=decision.confidence_value,
        executed=decision.should_execute
    )
```

---

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=confidence_gate

# Specific test
pytest tests/test_confidence_gate.py::test_high_confidence
```

---

## Documentation

- **API Reference:** [docs/api.md](docs/api.md)
- **Configuration:** [docs/configuration.md](docs/configuration.md)
- **Examples:** [examples/](examples/)
- **Troubleshooting:** [docs/troubleshooting.md](docs/troubleshooting.md)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Credits

Built by **Justice Apex LLC** as part of the Consciousness Architecture initiative.

> *Making autonomous systems safer, one decision at a time.*
