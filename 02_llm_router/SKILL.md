# LLMRouter Skill

## Overview
LLMRouter automatically routes queries to the best LLM provider (Gemini, Claude, OpenAI) based on cost, performance, and health metrics. Eliminates provider lock-in while optimizing for speed and cost.

## What It Does
- Routes queries to Gemini (cheapest), Claude (balanced), or OpenAI (most capable)
- Automatic failover when providers fail
- Tracks cost per provider
- Monitors provider health
- Caches responses to avoid redundant queries
- Supports streaming and async

## Use Cases
- Build without provider lock-in
- Cost-optimize intelligence queries
- Load balance across providers
- Automatic resilience
- Hybrid reasoning (different providers for different tasks)

## Key Features
- Multi-provider support (Gemini, Claude, OpenAI)
- Automatic provider selection
- Cost tracking and optimization
- Provider health monitoring
- Automatic failover
- Request deduplication via caching
- Thread-safe operations
- Metrics export

## Installation
```bash
openclaw install justice-apex/llm-router
```

## Quick Start
```python
from llm_router import LLMRouter

router = LLMRouter()

# Simple query (uses cheapest provider)
response = router.query("Analyze this whale trade")

print(f"Response: {response.text}")
print(f"Provider: {response.provider}")
print(f"Cost: ${response.cost:.4f}")
```

## Performance
- Query latency: 150-250ms
- Cached responses: <5ms
- Cost range: $0.01-$0.05 per 1k tokens
- Supports 100+ concurrent queries

## Requirements
- Python 3.8+
- API keys for providers (optional for simulation)

## Support
- GitHub Issues: https://github.com/justice-apex/skills/issues
- Documentation: https://docs.justice-apex.io/llm-router
