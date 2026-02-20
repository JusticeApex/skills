# ConfidenceGate API Reference

Complete API documentation for the ConfidenceGate confidence evaluation system.

## Table of Contents
- [Classes](#classes)
- [Enums](#enums)
- [Data Classes](#data-classes)
- [Methods](#methods)
- [Examples](#examples)

---

## Classes

### ConfidenceGate

The main class for evaluating action safety and managing decision history.

#### Constructor

```python
ConfidenceGate(
    storage_path: Optional[Path] = None,
    max_history: int = 10000
)
```

**Parameters:**
- `storage_path` (Path, optional): Directory for storing decision history
- `max_history` (int): Maximum decisions to keep in memory (default: 10,000)

**Attributes:**
- `rules` (Dict[str, ActionRule]): Registered action rules
- `history` (deque): Circular buffer of past decisions

**Example:**
```python
gate = ConfidenceGate(
    storage_path=Path("./gate_history"),
    max_history=5000
)
```

---

## Enums

### ActionConfidence

Confidence levels for actions.

```python
class ActionConfidence(Enum):
    HIGH = "high"       # Auto-execute immediately
    MEDIUM = "medium"   # Execute but log closely
    LOW = "low"         # Pause for human review
    CRITICAL = "critical"  # Always pause for approval
```

**Use Cases:**
- `HIGH`: Small trades, routine updates, safe operations
- `MEDIUM`: Normal transactions, standard deployments
- `LOW`: Uncommon operations, edge cases
- `CRITICAL`: Data deletions, security changes, irreversible ops

### RiskFactor

Risk factors that adjust confidence dynamically.

```python
class RiskFactor(Enum):
    VOLATILITY = "volatility"              # Market/system volatility
    ERROR_RATE = "error_rate"              # Recent error frequency
    LOSING_STREAK = "losing_streak"        # Consecutive failures
    UNKNOWN_CONDITION = "unknown_condition"  # Untested condition
    NEW_MARKET = "new_market"              # First time in market
    LARGE_AMOUNT = "large_amount"          # Large transaction size
```

---

## Data Classes

### ConfidenceScore

Result of action evaluation. Contains decision and reasoning.

```python
@dataclass
class ConfidenceScore:
    action: str
    base_confidence: ActionConfidence
    adjusted_confidence: ActionConfidence
    confidence_value: float  # 0.0 to 1.0
    should_execute: bool
    risk_factors: Dict[str, float] = {}
    adjustments: Dict[str, float] = {}
    explanation: str = ""
    timestamp: str = ""
```

**Fields:**
- `action`: Name of the action evaluated
- `base_confidence`: Original confidence level
- `adjusted_confidence`: Confidence after risk adjustments
- `confidence_value`: Numeric score (0.0-1.0)
- `should_execute`: Whether action should auto-execute
- `risk_factors`: Risk factors applied (0.0-1.0 scale)
- `adjustments`: Confidence reductions from each risk factor
- `explanation`: Human-readable decision summary
- `timestamp`: ISO 8601 timestamp of evaluation

**Methods:**
```python
score.to_dict() -> Dict
# Convert score to serializable dictionary
```

**Example:**
```python
score = gate.evaluate_action('trade', risk_factors={'volatility': 0.8})

print(f"Execute: {score.should_execute}")
print(f"Confidence: {score.confidence_value:.2%}")
print(f"Explanation: {score.explanation}")
```

### ActionRule

Configuration for an action type.

```python
@dataclass
class ActionRule:
    action: str
    base_confidence: ActionConfidence
    custom_threshold: Optional[float] = None
    risk_adjustments: Dict[RiskFactor, float] = {}
    override_allowed: bool = True
```

**Fields:**
- `action`: Action identifier
- `base_confidence`: Default confidence level
- `custom_threshold`: Override default execution threshold
- `risk_adjustments`: How each risk factor affects confidence
- `override_allowed`: Can force execute if paused

**Methods:**
```python
rule.get_threshold() -> float
# Get the execution threshold (0.0-1.0)
```

---

## Methods

### register_action

Register an action type with confidence level.

```python
def register_action(
    action: str,
    confidence: ActionConfidence,
    custom_threshold: Optional[float] = None,
    risk_adjustments: Optional[Dict[RiskFactor, float]] = None
) -> None
```

**Parameters:**
- `action`: Unique action identifier
- `confidence`: Base confidence level (HIGH/MEDIUM/LOW/CRITICAL)
- `custom_threshold`: Override default threshold (0.0-1.0)
- `risk_adjustments`: Map of risk factors to adjustment amounts

**Example:**
```python
gate.register_action(
    'make_trade',
    ActionConfidence.MEDIUM,
    custom_threshold=0.65,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,
        RiskFactor.LOSING_STREAK: 0.2,
        RiskFactor.LARGE_AMOUNT: 0.4
    }
)
```

### evaluate_action

Evaluate whether an action should execute.

```python
def evaluate_action(
    action: str,
    context: Optional[Dict[str, Any]] = None,
    risk_factors: Optional[Dict[str, float]] = None
) -> ConfidenceScore
```

**Parameters:**
- `action`: Action to evaluate
- `context`: Action context (optional metadata)
- `risk_factors`: Current risk factors (0.0-1.0 scale)

**Returns:** ConfidenceScore with decision

**Example:**
```python
score = gate.evaluate_action(
    'make_trade',
    context={'amount': 100, 'pair': 'BTC/USD'},
    risk_factors={
        'volatility': 0.72,
        'losing_streak': 0.3,
        'error_rate': 0.15
    }
)

if score.should_execute:
    execute_trade()
else:
    wait_for_approval()
```

### force_execute

Force execute an action that was paused (override).

```python
def force_execute(score: ConfidenceScore) -> bool
```

**Parameters:**
- `score`: ConfidenceScore to override

**Returns:** True if override allowed, False otherwise

**Example:**
```python
score = gate.evaluate_action('critical_op')

if not score.should_execute:
    # Human reviewed and approved
    if gate.force_execute(score):
        execute_critical_operation()
```

### get_history

Retrieve decision history.

```python
def get_history(
    action: Optional[str] = None,
    limit: int = 100
) -> List[ConfidenceScore]
```

**Parameters:**
- `action`: Filter by action type (None = all)
- `limit`: Maximum results to return

**Returns:** List of ConfidenceScore objects (newest first)

**Example:**
```python
# Get last 50 trade decisions
history = gate.get_history(action='make_trade', limit=50)

# Get all recent decisions
recent = gate.get_history(limit=100)
```

### get_statistics

Generate statistics on decision history.

```python
def get_statistics(action: Optional[str] = None) -> Dict[str, Any]
```

**Parameters:**
- `action`: Calculate stats for specific action (None = all)

**Returns:** Dictionary with statistics

**Statistics Returned:**
```python
{
    'total_decisions': int,        # Total decisions made
    'executed': int,               # Decisions that auto-executed
    'paused': int,                 # Decisions paused for review
    'execution_rate': float,       # Fraction auto-executed
    'avg_confidence': float,       # Average confidence (0.0-1.0)
    'min_confidence': float,       # Lowest confidence score
    'max_confidence': float        # Highest confidence score
}
```

**Example:**
```python
stats = gate.get_statistics(action='make_trade')

print(f"Total trades: {stats['total_decisions']}")
print(f"Success rate: {stats['execution_rate']:.1%}")
print(f"Average confidence: {stats['avg_confidence']:.2f}")
```

### save_history

Save decision history to disk.

```python
def save_history() -> None
```

**Format:** JSONL (one decision per line)

**Location:** `{storage_path}/history.jsonl`

**Example:**
```python
gate.save_history()
# Persists all decisions to history.jsonl
```

---

## Execution Thresholds

Default thresholds by confidence level:

| Level | Threshold | Behavior |
|-------|-----------|----------|
| HIGH | 0.7 | Usually auto-executes |
| MEDIUM | 0.5 | Execute if confident |
| LOW | 0.3 | Often paused |
| CRITICAL | 0.0 | Always paused |

Custom thresholds override these defaults:

```python
gate.register_action(
    'risky_trade',
    ActionConfidence.MEDIUM,
    custom_threshold=0.8  # Stricter than default 0.5
)
```

---

## Risk Factor Adjustments

Risk factors reduce confidence proportionally:

```python
adjustment = adjustment_amount * risk_level
```

Example:
```python
gate.register_action(
    'trade',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,    # 30% max reduction
        RiskFactor.LOSING_STREAK: 0.2   # 20% max reduction
    }
)

# Volatility = 0.8 → reduces confidence by 0.3 * 0.8 = 0.24
# Losing streak = 0.5 → reduces confidence by 0.2 * 0.5 = 0.1
# Total reduction: 0.34
```

---

## Confidence Value Conversions

Internal numeric conversions:

```
ActionConfidence.HIGH      → 0.8
ActionConfidence.MEDIUM    → 0.5
ActionConfidence.LOW       → 0.2
ActionConfidence.CRITICAL  → 0.0
```

Reverse conversions:
```
0.7+  → HIGH
0.4+  → MEDIUM
0.1+  → LOW
<0.1  → CRITICAL
```

---

## Thread Safety

All methods are thread-safe for concurrent use:

```python
gate = ConfidenceGate()

# Safe to use from multiple threads
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(gate.evaluate_action, 'trade')
        for _ in range(100)
    ]
```

---

## Error Handling

### ValueError: Unknown action

```python
gate.evaluate_action('unregistered_action')
# Raises ValueError: Unknown action: unregistered_action

# Fix: Register action first
gate.register_action('unregistered_action', ActionConfidence.MEDIUM)
```

### Invalid threshold

```python
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=1.5)
# Accepted (no validation), but will behave unexpectedly

# Best practice: Keep 0.0 <= custom_threshold <= 1.0
```

---

## Performance Characteristics

- **Evaluation latency:** <5ms per decision
- **Memory per action:** ~1KB per decision in history
- **Thread-safe:** Yes (uses RLock)
- **Max history:** Configurable (default 10,000 in memory)
- **Scalability:** 100,000+ actions without degradation

---

## Complete Example

```python
from confidence_gate import ConfidenceGate, ActionConfidence, RiskFactor
from pathlib import Path

# Initialize
gate = ConfidenceGate(storage_path=Path("./trading_history"))

# Register trading actions
gate.register_action(
    'buy_crypto',
    ActionConfidence.MEDIUM,
    custom_threshold=0.6,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,
        RiskFactor.LOSING_STREAK: 0.25,
        RiskFactor.LARGE_AMOUNT: 0.4
    }
)

gate.register_action(
    'sell_crypto',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.2,
        RiskFactor.UNKNOWN_CONDITION: 0.3
    }
)

# Evaluate a trade
market_conditions = {
    'volatility': 0.75,
    'losing_streak': 0.2,
    'large_amount': 0.0
}

score = gate.evaluate_action(
    'buy_crypto',
    context={'amount': 1.5, 'pair': 'BTC/USD'},
    risk_factors=market_conditions
)

print(f"Trade confidence: {score.confidence_value:.1%}")
print(f"Should execute: {score.should_execute}")
print(f"Explanation: {score.explanation}")

if score.should_execute:
    print("✅ AUTO-EXECUTING TRADE")
    execute_trade(1.5, 'BTC/USD')
else:
    print("⏸️  PAUSED - AWAITING APPROVAL")
    if await_human_approval():
        if gate.force_execute(score):
            execute_trade(1.5, 'BTC/USD')

# Analytics
stats = gate.get_statistics()
print(f"\nTrade Statistics:")
print(f"  Total: {stats['total_decisions']}")
print(f"  Auto-executed: {stats['execution_rate']:.1%}")
print(f"  Avg confidence: {stats['avg_confidence']:.2f}")

# Persistence
gate.save_history()
```

---

## See Also

- [Configuration Guide](configuration.md)
- [Troubleshooting](troubleshooting.md)
- [README](../README.md)
