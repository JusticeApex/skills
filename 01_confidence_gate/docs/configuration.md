# ConfidenceGate Configuration Guide

Complete guide to configuring ConfidenceGate for your use case.

## Table of Contents
- [Basic Configuration](#basic-configuration)
- [Risk Adjustment Strategies](#risk-adjustment-strategies)
- [Threshold Tuning](#threshold-tuning)
- [Domain-Specific Configs](#domain-specific-configs)
- [Advanced Configuration](#advanced-configuration)

---

## Basic Configuration

### Minimal Setup

```python
from confidence_gate import ConfidenceGate, ActionConfidence

gate = ConfidenceGate()

# Register one action
gate.register_action('my_action', ActionConfidence.MEDIUM)

# Evaluate
score = gate.evaluate_action('my_action')
```

### With Storage Path

```python
from pathlib import Path

gate = ConfidenceGate(
    storage_path=Path("./confidence_gate_data"),
    max_history=5000
)
```

### Parameters

| Parameter | Default | Range | Use |
|-----------|---------|-------|-----|
| `storage_path` | `./confidence_gate_history` | Path | Where to save history |
| `max_history` | 10,000 | 100-100,000 | Memory limit for decisions |

---

## Risk Adjustment Strategies

Risk adjustments control how much each risk factor reduces confidence.

### Conservative Strategy (Low Risk Tolerance)

Use for critical operations where safety is paramount:

```python
gate.register_action(
    'critical_operation',
    ActionConfidence.MEDIUM,
    custom_threshold=0.8,  # Higher threshold
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.5,          # Big impact
        RiskFactor.ERROR_RATE: 0.4,
        RiskFactor.LOSING_STREAK: 0.4,
        RiskFactor.UNKNOWN_CONDITION: 0.6,   # Very cautious
        RiskFactor.NEW_MARKET: 0.5,
        RiskFactor.LARGE_AMOUNT: 0.6
    }
)
```

### Aggressive Strategy (High Risk Tolerance)

Use for routine operations where speed matters:

```python
gate.register_action(
    'routine_trade',
    ActionConfidence.HIGH,
    custom_threshold=0.4,  # Lower threshold
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.1,          # Small impact
        RiskFactor.ERROR_RATE: 0.1,
        RiskFactor.LOSING_STREAK: 0.15,
        RiskFactor.UNKNOWN_CONDITION: 0.2,
        RiskFactor.NEW_MARKET: 0.1,
        RiskFactor.LARGE_AMOUNT: 0.2
    }
)
```

### Balanced Strategy (Default)

Middle ground for most operations:

```python
gate.register_action(
    'standard_operation',
    ActionConfidence.MEDIUM,
    custom_threshold=0.6,  # Medium threshold
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.25,
        RiskFactor.ERROR_RATE: 0.2,
        RiskFactor.LOSING_STREAK: 0.2,
        RiskFactor.UNKNOWN_CONDITION: 0.3,
        RiskFactor.NEW_MARKET: 0.25,
        RiskFactor.LARGE_AMOUNT: 0.3
    }
)
```

---

## Threshold Tuning

Thresholds determine when actions auto-execute.

### Default Thresholds

```python
# By confidence level
HIGH      → 0.7  (likely auto-execute)
MEDIUM    → 0.5  (maybe auto-execute)
LOW       → 0.3  (likely pause)
CRITICAL  → 0.0  (always pause)
```

### Custom Thresholds

Set stricter or looser thresholds:

```python
# Strict threshold - rarely auto-executes
gate.register_action(
    'high_value_trade',
    ActionConfidence.MEDIUM,
    custom_threshold=0.9  # Requires 90%+ confidence
)

# Loose threshold - usually auto-executes
gate.register_action(
    'low_value_trade',
    ActionConfidence.MEDIUM,
    custom_threshold=0.3  # Executes at 30%+ confidence
)
```

### Threshold Selection Guide

| Threshold | Execution Pattern | Use Case |
|-----------|-------------------|----------|
| 0.1-0.3 | Very permissive | Routine, low-risk |
| 0.4-0.6 | Balanced | Standard operations |
| 0.7-0.85 | Conservative | Important operations |
| 0.9+ | Extremely strict | Critical, irreversible |

---

## Domain-Specific Configs

### Trading Bot Configuration

```python
# Setup
gate = ConfidenceGate(storage_path=Path("./trading_gate"))

# Small trades - auto-execute readily
gate.register_action(
    'micro_trade',
    ActionConfidence.HIGH,
    custom_threshold=0.5,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.2,
        RiskFactor.LOSING_STREAK: 0.15,
        RiskFactor.ERROR_RATE: 0.1
    }
)

# Medium trades - need higher confidence
gate.register_action(
    'standard_trade',
    ActionConfidence.MEDIUM,
    custom_threshold=0.7,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,
        RiskFactor.LOSING_STREAK: 0.25,
        RiskFactor.ERROR_RATE: 0.2
    }
)

# Large trades - always review
gate.register_action(
    'macro_trade',
    ActionConfidence.LOW,
    custom_threshold=0.9,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.4,
        RiskFactor.LOSING_STREAK: 0.3,
        RiskFactor.ERROR_RATE: 0.25,
        RiskFactor.LARGE_AMOUNT: 0.5
    }
)
```

### Code Deployment Configuration

```python
gate = ConfidenceGate(storage_path=Path("./deployment_gate"))

# Test environment - auto-deploy
gate.register_action(
    'deploy_test',
    ActionConfidence.HIGH,
    risk_adjustments={
        RiskFactor.UNKNOWN_CONDITION: 0.2,
        RiskFactor.ERROR_RATE: 0.1
    }
)

# Staging - high confidence needed
gate.register_action(
    'deploy_staging',
    ActionConfidence.MEDIUM,
    custom_threshold=0.75,
    risk_adjustments={
        RiskFactor.UNKNOWN_CONDITION: 0.3,
        RiskFactor.ERROR_RATE: 0.2
    }
)

# Production - always manual
gate.register_action(
    'deploy_production',
    ActionConfidence.CRITICAL,
    override_allowed=True  # Can override after review
)
```

### Financial Operations Configuration

```python
gate = ConfidenceGate(storage_path=Path("./finance_gate"))

# Small payments - auto-process
gate.register_action(
    'payment_small',
    ActionConfidence.HIGH,
    custom_threshold=0.5,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.1,
        RiskFactor.ERROR_RATE: 0.15
    }
)

# Large transfers - require approval
gate.register_action(
    'payment_large',
    ActionConfidence.CRITICAL,
    override_allowed=True,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,
        RiskFactor.ERROR_RATE: 0.25,
        RiskFactor.LARGE_AMOUNT: 0.6
    }
)

# International transfers - always manual
gate.register_action(
    'payment_international',
    ActionConfidence.CRITICAL,
    override_allowed=True,
    risk_adjustments={
        RiskFactor.UNKNOWN_CONDITION: 0.5,
        RiskFactor.NEW_MARKET: 0.4
    }
)
```

---

## Advanced Configuration

### Dynamic Risk Adjustment

Adjust risk factors based on system state:

```python
class AdaptiveGate:
    def __init__(self):
        self.gate = ConfidenceGate()
        self.gate.register_action('trade', ActionConfidence.MEDIUM)
    
    def evaluate_with_context(self, market_state):
        """Evaluate trade based on market conditions"""
        
        # Calculate risk factors from market state
        risk_factors = {
            'volatility': market_state.volatility,
            'error_rate': market_state.recent_errors / max(1, market_state.total_trades),
            'losing_streak': min(1.0, market_state.consecutive_losses / 10),
            'large_amount': 1.0 if market_state.trade_size > 10000 else 0.3
        }
        
        return self.gate.evaluate_action(
            'trade',
            risk_factors=risk_factors
        )
```

### Multi-Action Configuration Factory

```python
def setup_trading_gate(risk_profile='balanced'):
    """Setup gate based on risk profile"""
    
    gate = ConfidenceGate()
    
    profiles = {
        'conservative': {
            'threshold': 0.8,
            'volatility': 0.4,
            'losing_streak': 0.3,
            'error_rate': 0.25
        },
        'balanced': {
            'threshold': 0.6,
            'volatility': 0.25,
            'losing_streak': 0.2,
            'error_rate': 0.15
        },
        'aggressive': {
            'threshold': 0.4,
            'volatility': 0.1,
            'losing_streak': 0.1,
            'error_rate': 0.05
        }
    }
    
    config = profiles[risk_profile]
    
    for size in ['micro', 'small', 'standard']:
        gate.register_action(
            f'{size}_trade',
            ActionConfidence.MEDIUM,
            custom_threshold=config['threshold'],
            risk_adjustments={
                RiskFactor.VOLATILITY: config['volatility'],
                RiskFactor.LOSING_STREAK: config['losing_streak'],
                RiskFactor.ERROR_RATE: config['error_rate']
            }
        )
    
    return gate
```

### Confidence Curves

Control how risk impacts confidence:

```python
# Linear relationship (default)
adjustment = adjustment_amount * risk_level

# Quadratic relationship (more sensitive to high risk)
adjustment = adjustment_amount * (risk_level ** 2)

# Logarithmic relationship (less sensitive at extremes)
import math
adjustment = adjustment_amount * math.log(1 + risk_level)
```

---

## Configuration Best Practices

### 1. Start Conservative

Begin with high thresholds and high risk adjustments, then relax:

```python
# Start here
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.9)

# Then gradually lower as you gain confidence
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.7)
```

### 2. Monitor History

Regular statistics help tune configuration:

```python
stats = gate.get_statistics()
execution_rate = stats['execution_rate']

# Adjust threshold if execution rate is too high/low
if execution_rate > 0.9:
    # Too permissive - raise threshold
    pass
elif execution_rate < 0.3:
    # Too strict - lower threshold
    pass
```

### 3. Test New Configurations

Test changes on historical data before deploying:

```python
# Original
old_gate = create_production_gate()

# New test config
test_gate = ConfidenceGate()
test_gate.register_action('trade', ActionConfidence.MEDIUM, custom_threshold=0.5)

# Compare on historical decisions
# ...
```

### 4. Document Your Choices

Keep a config file with rationale:

```python
# config.py
"""
Trading Gate Configuration
=============================

Risk Profile: Conservative (safety first)
Rationale: Early-stage trading, learning phase

Thresholds:
- Micro trades: 0.4 (low risk, frequent learning)
- Standard trades: 0.7 (balanced approach)
- Macro trades: 0.9 (rare, require approval)

Risk Adjustments:
- Volatility: HIGH impact (0.3-0.4)
  Reason: Volatile markets are less predictable
  
- Losing streak: HIGH impact (0.25-0.3)
  Reason: Need to rebuild confidence after losses
  
- Error rate: MEDIUM impact (0.15-0.25)
  Reason: System errors reduce trust
"""
```

---

## See Also

- [API Reference](api.md)
- [Troubleshooting](troubleshooting.md)
- [README](../README.md)
