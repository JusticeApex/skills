# EvolutionEngine - Autonomous Self-Improvement System

Enables autonomous systems to learn from outcomes, identify winning strategies, and automatically evolve without human intervention.

## Key Benefits

- **Autonomous Learning**: System improves itself in real-time
- **Pattern Detection**: Identifies successful strategies automatically
- **Strategy Evolution**: Creates variants of winning approaches
- **Genealogy Tracking**: Remember what works and why
- **Zero Human Intervention**: Runs continuously without direction
- **Production Ready**: Persists to disk, thread-safe

## Installation

```bash
pip install justice-apex-evolution-engine
```

## Quick Start

```python
from evolution_engine import EvolutionEngine

engine = EvolutionEngine()

# Create a strategy
strategy = engine.create_strategy("my_trading_strategy")

# Record outcomes
engine.record_outcome(strategy, success=True, reward=100)
engine.record_outcome(strategy, success=True, reward=95)
engine.record_outcome(strategy, success=False, reward=0)

# Get best performing strategy
best = engine.get_best_strategy()
engine.apply_strategy(best)

# Evolve: create variants of winning strategies
variant = engine.evolve()
```

## How It Works

1. **Record Outcomes**: Every strategy attempt is recorded with success/failure
2. **Pattern Detection**: Identifies strategies with >90% success rate
3. **Create Variants**: Generates improved versions of winners
4. **Automatic Application**: Deploys best performers immediately
5. **Continuous Learning**: Repeats forever, improving each cycle

## Example: Self-Improving Trading Bot

```python
engine = EvolutionEngine(success_threshold=0.85, min_attempts=20)

# Create initial strategies
s1 = engine.create_strategy("ma_crossover")
s2 = engine.create_strategy("rsi_oversold")
s3 = engine.create_strategy("bollinger_bands")

# Run trading
for trade in market_data:
    # Pick best current strategy
    best = engine.get_best_strategy()
    signal = strategies[best].generate_signal(trade)
    
    # Execute trade
    result = execute_trade(signal)
    
    # Record outcome
    engine.record_outcome(best, success=result.profitable, reward=result.profit)
    
    # Evolve every 100 trades
    if trade.count % 100 == 0:
        variant = engine.evolve()
        strategies[variant] = create_strategy_variant(strategies[best])

# Check final stats
stats = engine.get_statistics()
```

## Genealogy & Generation Tracking

```python
# Create lineage of strategies
g1 = engine.create_strategy("generation_1")
g2 = engine.create_variant(g1, "generation_2")
g3 = engine.create_variant(g2, "generation_3")

# Check genealogy
genealogy = engine.get_genealogy(g3)
print(f"Generation: {genealogy['generation']}")  # 3
print(f"Parent: {genealogy['parent_id']}")        # g2
```

## Performance

- Strategy creation: <1ms
- Outcome recording: <1ms
- Evolution cycles: <10ms
- Supports 10,000+ strategies in memory

## Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Testing

```bash
pytest tests/test_evolution_engine.py -v
```

## License

MIT - Open source and free for commercial use
