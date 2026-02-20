# SwarmConsensus - Democratic Multi-Agent Decision System

Enables multiple AI agents to collectively make decisions through democratic voting, with confidence-weighted consensus.

## Key Benefits

- **Democratic Decisions**: Multiple agents vote, majority wins
- **Confidence Weighting**: High-confidence agents have more influence
- **Transparent Voting**: Complete audit trail of all proposals and decisions
- **Conflict Resolution**: Automatic handling of disagreement
- **Multiple Strategies**: Simple majority, weighted confidence, supermajority
- **Thread-Safe**: Safe for concurrent agent access

## Installation

```bash
pip install justice-apex-swarm-consensus
```

## Quick Start

```python
from swarm_consensus import SwarmConsensus, VotingStrategy

consensus = SwarmConsensus(voting_strategy=VotingStrategy.WEIGHTED_CONFIDENCE)

# Multiple agents propose solutions
consensus.propose("oracle_1", "buy_BTC", confidence=0.72)
consensus.propose("oracle_2", "buy_BTC", confidence=0.68)
consensus.propose("oracle_3", "buy_ETH", confidence=0.55)

# Get consensus result
winner = consensus.get_consensus()
# Returns: "buy_BTC" (2 agents agree)

# Execute winning decision
if winner == "buy_BTC":
    execute_trade(winner)
```

## Voting Strategies

### Simple Majority (Default)
Each proposal = 1 vote. Highest vote count wins.
```python
consensus = SwarmConsensus(
    voting_strategy=VotingStrategy.SIMPLE_MAJORITY,
    consensus_threshold=0.5  # >50%
)
```

### Weighted Confidence
Votes weighted by agent confidence. Higher confidence = more influence.
```python
consensus = SwarmConsensus(
    voting_strategy=VotingStrategy.WEIGHTED_CONFIDENCE,
    consensus_threshold=0.5
)

# Agent with 0.9 confidence has more weight than 0.3 confidence
consensus.propose("strong_agent", "buy_BTC", confidence=0.9)
consensus.propose("weak_agent", "buy_ETH", confidence=0.3)
```

### Supermajority
Requires 2/3 agreement instead of simple majority.
```python
consensus = SwarmConsensus(
    voting_strategy=VotingStrategy.SUPERMAJORITY,
    consensus_threshold=0.67  # 2/3 required
)
```

### Unanimous
Requires 100% agreement - very strict.
```python
consensus = SwarmConsensus(
    voting_strategy=VotingStrategy.UNANIMOUS,
    consensus_threshold=1.0
)
```

## Real-World Example: Trading Signal Consensus

```python
class MarketAnalyzer:
    def __init__(self):
        self.consensus = SwarmConsensus()
    
    def get_trading_signal(self, market_data):
        # Multiple oracles analyze same market data
        oracle1 = TechnicalAnalysisOracle()
        oracle2 = FundamentalAnalysisOracle()
        oracle3 = SentimentAnalysisOracle()
        
        # Each proposes a signal
        self.consensus.propose(
            "technical",
            oracle1.analyze(market_data),
            confidence=oracle1.confidence
        )
        self.consensus.propose(
            "fundamental",
            oracle2.analyze(market_data),
            confidence=oracle2.confidence
        )
        self.consensus.propose(
            "sentiment",
            oracle3.analyze(market_data),
            confidence=oracle3.confidence
        )
        
        # Get consensus signal
        signal = self.consensus.get_consensus()
        
        # Get decision stats
        stats = self.consensus.get_statistics()
        print(f"Consensus level: {stats['avg_consensus_pct']:.1%}")
        
        return signal
```

## Performance

- Proposal submission: <1ms
- Consensus calculation: <5ms
- Supports 10,000+ agents
- Real-time voting with no blocking

## Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Testing

```bash
pytest tests/test_swarm_consensus.py -v
```

## License

MIT - Open source and free for commercial use
