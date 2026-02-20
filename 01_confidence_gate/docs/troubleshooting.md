# ConfidenceGate Troubleshooting Guide

Solutions to common issues and debugging tips.

## Table of Contents
- [Evaluation Issues](#evaluation-issues)
- [History Issues](#history-issues)
- [Performance Issues](#performance-issues)
- [Edge Cases](#edge-cases)
- [FAQ](#faq)

---

## Evaluation Issues

### Problem: "Unknown action" Error

```python
ValueError: Unknown action: my_action
```

**Causes:**
1. Action not registered before evaluation
2. Typo in action name
3. Case sensitivity mismatch

**Solutions:**

```python
# ❌ Wrong - action not registered
score = gate.evaluate_action('my_action')

# ✅ Correct - register first
gate.register_action('my_action', ActionConfidence.MEDIUM)
score = gate.evaluate_action('my_action')

# Check registered actions
if 'my_action' in gate.rules:
    score = gate.evaluate_action('my_action')
else:
    gate.register_action('my_action', ActionConfidence.MEDIUM)
```

### Problem: Action Always Executes

Everything passes when it shouldn't.

**Diagnosis:**
```python
score = gate.evaluate_action('test')
print(f"Threshold: {gate.rules['test'].get_threshold()}")
print(f"Confidence: {score.confidence_value}")
print(f"Execute: {score.should_execute}")
```

**Solutions:**

1. **Raise the threshold:**
```python
# Too permissive
gate.register_action('test', ActionConfidence.MEDIUM)  # threshold=0.5

# Better - explicit threshold
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.8)
```

2. **Add risk factors:**
```python
gate.register_action(
    'test',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.3,
        RiskFactor.ERROR_RATE: 0.3
    }
)

# Include risk in evaluation
score = gate.evaluate_action(
    'test',
    risk_factors={'volatility': 0.8, 'error_rate': 0.5}
)
```

3. **Change base confidence:**
```python
# HIGH automatically executes more
gate.register_action('test', ActionConfidence.HIGH)

# LOW more cautious
gate.register_action('test', ActionConfidence.LOW)
```

### Problem: Action Never Executes

Everything pauses when some should execute.

**Diagnosis:**
```python
score = gate.evaluate_action('test')
print(f"Base: {score.base_confidence}")
print(f"Threshold: {gate.rules['test'].get_threshold()}")
print(f"Confidence: {score.confidence_value}")
print(f"Risk factors: {score.risk_factors}")
print(f"Adjustments: {score.adjustments}")
```

**Solutions:**

1. **Lower the threshold:**
```python
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.3)
```

2. **Reduce risk adjustments:**
```python
gate.register_action(
    'test',
    ActionConfidence.MEDIUM,
    risk_adjustments={
        RiskFactor.VOLATILITY: 0.1,  # Less impact
        RiskFactor.ERROR_RATE: 0.05
    }
)
```

3. **Use higher base confidence:**
```python
gate.register_action('test', ActionConfidence.HIGH)
```

4. **Check risk factors aren't too high:**
```python
# Risk factors should be 0.0-1.0
score = gate.evaluate_action(
    'test',
    risk_factors={
        'volatility': 0.5,      # ✅ Good
        'error_rate': 1.5       # ❌ Too high (should be 0.0-1.0)
    }
)
```

### Problem: Inconsistent Results

Same action, different decisions.

**Causes:**
1. Risk factors are changing
2. Threshold configuration changed
3. Thread safety issue

**Solutions:**

```python
# 1. Check risk factors
score1 = gate.evaluate_action('test')
score2 = gate.evaluate_action('test', risk_factors={'volatility': 0.5})

# Different risk factors → different results (expected)

# 2. Check threshold wasn't overwritten
original_threshold = gate.rules['test'].get_threshold()
gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.9)
new_threshold = gate.rules['test'].get_threshold()

# 3. Check thread safety
# ConfidenceGate is thread-safe, but be careful with mutable risk factors

# ❌ Don't mutate risk_factors dict
risk_factors = {'volatility': 0.5}
gate.evaluate_action('test', risk_factors=risk_factors)
risk_factors['volatility'] = 0.9  # Don't modify!

# ✅ Create new dict each time
gate.evaluate_action('test', risk_factors={'volatility': 0.9})
```

---

## History Issues

### Problem: History Growing Too Large

Memory usage increases over time.

**Causes:**
1. max_history not configured
2. Evaluation happening faster than cleanup
3. Storage file growing

**Solutions:**

```python
# 1. Set max_history limit
gate = ConfidenceGate(max_history=5000)  # Keep only 5000 in memory

# 2. Archive old history periodically
if len(gate.history) > 8000:
    gate.save_history()
    # Clear and continue

# 3. Check storage file size
import os
history_size = os.path.getsize("confidence_gate_history/history.jsonl")
print(f"History file: {history_size / 1024 / 1024:.1f} MB")

# 4. Rotate history files
import shutil
from datetime import datetime

if history_size > 100 * 1024 * 1024:  # If >100MB
    timestamp = datetime.now().isoformat()
    archive_path = f"confidence_gate_history/archive_{timestamp}.jsonl"
    shutil.move("confidence_gate_history/history.jsonl", archive_path)
    gate = ConfidenceGate()  # Start fresh
```

### Problem: History Not Saving

Decisions lost after restart.

**Causes:**
1. storage_path doesn't exist
2. save_history() not called
3. Permission issues

**Solutions:**

```python
# 1. Ensure path exists
from pathlib import Path

path = Path("./gate_history")
path.mkdir(parents=True, exist_ok=True)

gate = ConfidenceGate(storage_path=path)

# 2. Explicitly save (not automatic)
gate.evaluate_action('test')
gate.save_history()  # Must call this!

# 3. Verify file was created
history_file = path / "history.jsonl"
assert history_file.exists()

# 4. Check permissions
import os
assert os.access(path, os.W_OK)

# 5. Auto-save periodically
import atexit

def save_on_exit():
    gate.save_history()

atexit.register(save_on_exit)
```

### Problem: History Not Loading

Decisions from previous session lost.

**Causes:**
1. Different storage_path used
2. History file corrupted
3. Wrong working directory

**Solutions:**

```python
# 1. Use same storage_path
path = Path("./gate_history")

# Create with path
gate = ConfidenceGate(storage_path=path)

# Verify history loaded
print(f"Loaded {len(gate.history)} decisions")

# 2. Check file exists and is readable
history_file = path / "history.jsonl"
if not history_file.exists():
    print("History file not found - starting fresh")

# 3. Validate history file
if history_file.exists():
    with open(history_file) as f:
        for i, line in enumerate(f):
            try:
                json.loads(line)
            except json.JSONDecodeError:
                print(f"Corrupted line {i}: {line}")

# 4. Check working directory
print(f"Current directory: {os.getcwd()}")
print(f"History path: {path.absolute()}")
```

---

## Performance Issues

### Problem: Slow Evaluation

Evaluation taking too long.

**Targets:**
- Typical evaluation: <5ms
- With risk factors: <10ms

**Diagnosis:**
```python
import time

start = time.perf_counter()
score = gate.evaluate_action('test', risk_factors={'volatility': 0.5})
elapsed = (time.perf_counter() - start) * 1000

if elapsed > 10:
    print(f"WARNING: Slow evaluation ({elapsed:.1f}ms)")
```

**Solutions:**

```python
# 1. Reduce history size (if storing large history)
gate = ConfidenceGate(max_history=1000)  # Smaller limit

# 2. Cache rule lookups
gate.register_action('test', ActionConfidence.MEDIUM)
rule = gate.rules['test']

# Multiple evaluations with same rule
for _ in range(100):
    score = gate.evaluate_action('test')

# 3. Batch operations
risk_factors = [{'volatility': i*0.1} for i in range(10)]
scores = [gate.evaluate_action('test', risk_factors=rf) for rf in risk_factors]

# 4. Profile to find bottleneck
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

for _ in range(1000):
    gate.evaluate_action('test')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Problem: High Memory Usage

Gate consuming too much RAM.

**Solutions:**

```python
# 1. Reduce max_history
gate = ConfidenceGate(max_history=1000)

# 2. Clear history periodically
if len(gate.history) > 5000:
    gate.history.clear()
    gate.save_history()

# 3. Use smaller risk_factors dict
# ❌ Big dict
large_factors = {f'factor_{i}': 0.1 for i in range(100)}
score = gate.evaluate_action('test', risk_factors=large_factors)

# ✅ Only relevant factors
small_factors = {'volatility': 0.5}
score = gate.evaluate_action('test', risk_factors=small_factors)

# 4. Monitor memory
import tracemalloc

tracemalloc.start()
gate.evaluate_action('test')
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.1f} MB")
```

---

## Edge Cases

### Problem: Invalid Risk Factor Values

Risk factors should be 0.0-1.0.

**Solution:**
```python
# Clamp risk factors to valid range
def validate_risk_factors(risk_factors):
    return {
        k: max(0.0, min(1.0, v))
        for k, v in risk_factors.items()
    }

score = gate.evaluate_action(
    'test',
    risk_factors=validate_risk_factors({'volatility': 1.5})
)
```

### Problem: Invalid Custom Threshold

Threshold outside 0.0-1.0 range.

**Solution:**
```python
# Validate and clamp threshold
def validate_threshold(threshold):
    return max(0.0, min(1.0, threshold))

gate.register_action(
    'test',
    ActionConfidence.MEDIUM,
    custom_threshold=validate_threshold(1.5)
)
```

### Problem: Concurrent Modifications

Thread safety with register_action.

**Solution:**
```python
# Gate handles locks automatically
gate = ConfidenceGate()

def register_actions():
    for i in range(100):
        gate.register_action(f'action_{i}', ActionConfidence.MEDIUM)

from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(register_actions) for _ in range(5)]
    for f in futures:
        f.result()

print(f"Total actions: {len(gate.rules)}")  # Should be 500
```

---

## FAQ

### Q: How do I reset the gate?

```python
# Create new instance
gate = ConfidenceGate()

# Or clear history
gate.history.clear()
```

### Q: Can I change confidence level after registering?

```python
# Re-register with new level
gate.register_action('test', ActionConfidence.HIGH)
```

### Q: How do I export history as CSV?

```python
import csv

history = gate.get_history()
with open('history.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['action', 'confidence_value', 'should_execute'])
    writer.writeheader()
    for score in history:
        writer.writerow({
            'action': score.action,
            'confidence_value': score.confidence_value,
            'should_execute': score.should_execute
        })
```

### Q: What's the max number of actions I can register?

Theoretically unlimited. Practically:
- 1,000+ actions: No issues
- 10,000+ actions: Consider sharding across instances
- 100,000+ actions: Use dedicated backend

### Q: Can I use with asyncio?

Yes, but no built-in async support:

```python
import asyncio

async def evaluate_async(gate, action):
    # evaluate_action is synchronous but fast (<5ms)
    return gate.evaluate_action(action)

async def main():
    gate = ConfidenceGate()
    gate.register_action('test', ActionConfidence.MEDIUM)
    
    results = await asyncio.gather(
        evaluate_async(gate, 'test'),
        evaluate_async(gate, 'test'),
    )
    return results

asyncio.run(main())
```

### Q: How do I test new configurations?

```python
# Create test gate
test_gate = ConfidenceGate()
test_gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.8)

# Create prod gate
prod_gate = ConfidenceGate()
prod_gate.register_action('test', ActionConfidence.MEDIUM, custom_threshold=0.5)

# Compare on same decisions
test_decisions = []
prod_decisions = []

for i in range(100):
    test_score = test_gate.evaluate_action('test')
    prod_score = prod_gate.evaluate_action('test')
    
    if test_score.should_execute != prod_score.should_execute:
        print(f"Decision difference at evaluation {i}")
```

---

## Getting Help

If you still have issues:

1. **Check logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Print debug info:**
```python
score = gate.evaluate_action('test')
print(f"Action: {score.action}")
print(f"Base: {score.base_confidence}")
print(f"Adjusted: {score.adjusted_confidence}")
print(f"Confidence: {score.confidence_value:.2f}")
print(f"Threshold: {gate.rules[score.action].get_threshold():.2f}")
print(f"Execute: {score.should_execute}")
print(f"Explanation: {score.explanation}")
```

3. **Check statistics:**
```python
stats = gate.get_statistics()
for key, value in stats.items():
    print(f"{key}: {value}")
```

4. **Open an issue:**
- GitHub: https://github.com/justice-apex/skills/issues
- Include reproducible code
- Include output of debug commands above
