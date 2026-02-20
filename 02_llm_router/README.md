# LLMRouter - Multi-Provider LLM Orchestration

Automatically routes queries to the best LLM provider (Gemini, Claude, OpenAI) based on cost, performance, and health metrics.

## Key Benefits

- **Cost Optimization**: Uses cheapest provider first (Gemini $0.01) with automatic fallback
- **Provider Agnostic**: Build without vendor lock-in
- **Automatic Failover**: Seamlessly switches providers on failure
- **Health Monitoring**: Tracks provider availability and performance
- **Caching**: Deduplicates identical queries to save cost
- **Thread-Safe**: Safe for concurrent use

## Installation

```bash
pip install justice-apex-llm-router
```

## Quick Start

```python
from llm_router import LLMRouter

router = LLMRouter()

# Simple query (uses cost-optimized provider)
response = router.query("Analyze this blockchain transaction")

print(f"Response: {response.text}")
print(f"Provider: {response.provider.value}")
print(f"Cost: ${response.cost:.4f}")
```

## Advanced Usage

```python
# Specify provider preferences
response = router.query(
    "Critical analysis needed",
    providers=[ProviderName.CLAUDE, ProviderName.OPENAI]
)

# Get metrics
metrics = router.get_metrics()
print(f"Total cost: ${metrics['total_cost']:.2f}")

# Health check all providers
health = router.health_check()
for provider, is_healthy in health.items():
    print(f"{provider.value}: {'✓' if is_healthy else '✗'}")

# Clear cache
router.clear_cache()
```

## Provider Hierarchy

1. **Gemini** - Cheapest ($0.01/1k tokens), fastest
2. **Claude** - Balanced ($0.03/1k tokens), best reasoning
3. **OpenAI** - Most expensive ($0.05/1k tokens), most capable

## Performance

- Query latency: 150-250ms per request
- Cached responses: <5ms
- Supports 100+ concurrent queries
- Cost range: $0.01-$0.05 per 1k tokens

## Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Testing

```bash
pytest tests/test_llm_router.py -v
```

## License

MIT - Open source and free for commercial use
