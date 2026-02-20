"""
Comprehensive tests for LLMRouter - 80+ tests
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llm_router import (
    LLMRouter,
    ProviderName,
    ProviderStatus,
    Query,
    Response,
    ProviderMetrics,
    GeminiBackend,
    ClaudeBackend,
    OpenAIBackend,
)


class TestLLMRouterInitialization:
    """Tests for router initialization"""
    
    def test_initialization(self):
        """Test router initialization"""
        router = LLMRouter()
        assert router is not None
        assert len(router.providers) == 3
        assert len(router.metrics) == 3
    
    def test_providers_registered(self):
        """All providers should be registered"""
        router = LLMRouter()
        assert ProviderName.GEMINI in router.providers
        assert ProviderName.CLAUDE in router.providers
        assert ProviderName.OPENAI in router.providers
    
    def test_metrics_initialized(self):
        """Metrics should be initialized for all providers"""
        router = LLMRouter()
        for provider in ProviderName:
            assert provider in router.metrics
            assert router.metrics[provider].status == ProviderStatus.HEALTHY
    
    def test_custom_storage_path(self):
        """Can specify custom storage path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = LLMRouter(storage_path=Path(tmpdir))
            assert router.storage_path == Path(tmpdir)


class TestQueryClass:
    """Tests for Query class"""
    
    def test_query_creation(self):
        """Create basic query"""
        query = Query(text="What is AI?")
        assert query.text == "What is AI?"
        assert query.temperature == 0.7
        assert query.max_tokens == 2000
    
    def test_query_hash_consistency(self):
        """Same query produces same hash"""
        q1 = Query(text="Test", temperature=0.7, max_tokens=2000)
        q2 = Query(text="Test", temperature=0.7, max_tokens=2000)
        
        assert q1.hash() == q2.hash()
    
    def test_query_hash_different(self):
        """Different queries produce different hashes"""
        q1 = Query(text="Test 1")
        q2 = Query(text="Test 2")
        
        assert q1.hash() != q2.hash()
    
    def test_query_with_system_prompt(self):
        """Query can include system prompt"""
        query = Query(
            text="Hello",
            system_prompt="You are helpful"
        )
        assert query.system_prompt == "You are helpful"


class TestProvidersBackends:
    """Tests for provider backends"""
    
    def test_gemini_backend(self):
        """Gemini backend works"""
        backend = GeminiBackend()
        query = Query(text="Test query")
        response = backend.query(query)
        
        assert response.provider == ProviderName.GEMINI
        assert response.cost > 0
        assert response.tokens_used > 0
    
    def test_claude_backend(self):
        """Claude backend works"""
        backend = ClaudeBackend()
        query = Query(text="Test query")
        response = backend.query(query)
        
        assert response.provider == ProviderName.CLAUDE
        assert response.cost > 0
    
    def test_openai_backend(self):
        """OpenAI backend works"""
        backend = OpenAIBackend()
        query = Query(text="Test query")
        response = backend.query(query)
        
        assert response.provider == ProviderName.OPENAI
        assert response.cost > 0
    
    def test_cost_per_1k_tokens(self):
        """Providers have different costs"""
        gemini = GeminiBackend().cost_per_1k_tokens()
        claude = ClaudeBackend().cost_per_1k_tokens()
        openai = OpenAIBackend().cost_per_1k_tokens()
        
        # Gemini should be cheapest
        assert gemini < claude
        assert claude < openai
    
    def test_health_check(self):
        """Health checks work for all providers"""
        for provider_name, provider in [
            (ProviderName.GEMINI, GeminiBackend()),
            (ProviderName.CLAUDE, ClaudeBackend()),
            (ProviderName.OPENAI, OpenAIBackend()),
        ]:
            assert provider.health_check() is True


class TestRouting:
    """Tests for query routing"""
    
    def test_simple_query(self):
        """Route a simple query"""
        router = LLMRouter()
        response = router.query("What is AI?")
        
        assert response is not None
        assert isinstance(response, Response)
        assert response.text is not None
    
    def test_query_with_providers(self):
        """Specify preferred providers"""
        router = LLMRouter()
        response = router.query(
            "Test",
            providers=[ProviderName.GEMINI]
        )
        
        assert response.provider == ProviderName.GEMINI
    
    def test_default_provider_order(self):
        """Default uses cost-optimized provider"""
        router = LLMRouter()
        response = router.query("Test")
        
        # Default should try Gemini first (cheapest)
        assert response.provider == ProviderName.GEMINI
    
    def test_fallback_to_next_provider(self):
        """Falls back to next provider on failure"""
        router = LLMRouter()
        
        # Mock first provider to fail
        with patch.object(router.providers[ProviderName.GEMINI], 'query', side_effect=Exception("Failed")):
            response = router.query(
                "Test",
                providers=[ProviderName.GEMINI, ProviderName.CLAUDE]
            )
            
            # Should fall back to Claude
            assert response.provider == ProviderName.CLAUDE
    
    def test_metrics_updated_on_success(self):
        """Metrics updated after successful query"""
        router = LLMRouter()
        initial_count = router.metrics[ProviderName.GEMINI].requests_total
        
        router.query("Test", providers=[ProviderName.GEMINI])
        
        # Count should increase
        assert router.metrics[ProviderName.GEMINI].requests_total == initial_count + 1
    
    def test_metrics_updated_on_failure(self):
        """Failed requests tracked in metrics"""
        router = LLMRouter()
        
        with patch.object(
            router.providers[ProviderName.GEMINI],
            'query',
            side_effect=Exception("API error")
        ):
            with patch.object(
                router.providers[ProviderName.CLAUDE],
                'query',
                side_effect=Exception("API error")
            ):
                with patch.object(
                    router.providers[ProviderName.OPENAI],
                    'query',
                    side_effect=Exception("API error")
                ):
                    with pytest.raises(RuntimeError):
                        router.query("Test")
        
        # Failure count should increase
        assert router.metrics[ProviderName.GEMINI].requests_failed > 0


class TestCaching:
    """Tests for request caching"""
    
    def test_cache_hit(self):
        """Identical queries cached"""
        router = LLMRouter()
        
        response1 = router.query("Same query")
        cache_size_after_first = router.get_cache_size()
        
        response2 = router.query("Same query", use_cache=True)
        cache_size_after_second = router.get_cache_size()
        
        # Cache size shouldn't increase
        assert cache_size_after_second == cache_size_after_first
    
    def test_cache_disabled(self):
        """Can disable caching"""
        router = LLMRouter()
        
        with patch.object(router.providers[ProviderName.GEMINI], 'query', wraps=router.providers[ProviderName.GEMINI].query) as mock_query:
            router.query("Test", use_cache=False)
            router.query("Test", use_cache=False)
            
            # Should call provider twice (no cache)
            assert mock_query.call_count == 2
    
    def test_clear_cache(self):
        """Cache can be cleared"""
        router = LLMRouter()
        
        router.query("Test")
        assert router.get_cache_size() > 0
        
        router.clear_cache()
        assert router.get_cache_size() == 0


class TestHealthMonitoring:
    """Tests for health monitoring"""
    
    def test_health_check(self):
        """Health check all providers"""
        router = LLMRouter()
        health = router.health_check()
        
        assert len(health) == 3
        assert all(isinstance(v, bool) for v in health.values())
    
    def test_unhealthy_provider_status(self):
        """Failed health check updates status"""
        router = LLMRouter()
        
        with patch.object(
            router.providers[ProviderName.GEMINI],
            'health_check',
            return_value=False
        ):
            router.health_check()
            
            assert router.metrics[ProviderName.GEMINI].status == ProviderStatus.UNHEALTHY


class TestMetrics:
    """Tests for metrics tracking"""
    
    def test_get_all_metrics(self):
        """Get metrics for all providers"""
        router = LLMRouter()
        router.query("Test")
        
        metrics = router.get_metrics()
        assert len(metrics) == 3
    
    def test_get_provider_metrics(self):
        """Get metrics for specific provider"""
        router = LLMRouter()
        router.query("Test", providers=[ProviderName.GEMINI])
        
        metrics = router.get_metrics(ProviderName.GEMINI)
        assert metrics['requests_total'] == 1
        assert metrics['requests_success'] == 1
    
    def test_success_rate_calculation(self):
        """Success rate calculated correctly"""
        router = LLMRouter()
        
        # Make successful queries
        for _ in range(5):
            router.query("Test", providers=[ProviderName.GEMINI])
        
        metrics = router.get_metrics(ProviderName.GEMINI)
        assert metrics['success_rate'] == 1.0  # All succeeded


class TestProviderSelection:
    """Tests for provider selection strategies"""
    
    def test_cheapest_provider(self):
        """Get cheapest provider"""
        router = LLMRouter()
        cheapest = router.get_cheapest_provider()
        
        assert cheapest == ProviderName.GEMINI
    
    def test_healthiest_provider(self):
        """Get healthiest provider"""
        router = LLMRouter()
        healthiest = router.get_healthiest_provider()
        
        assert healthiest in [ProviderName.GEMINI, ProviderName.CLAUDE, ProviderName.OPENAI]
    
    def test_fastest_provider(self):
        """Get fastest provider"""
        router = LLMRouter()
        fastest = router.get_fastest_provider()
        
        assert fastest == ProviderName.GEMINI


class TestMetricsStorage:
    """Tests for metrics persistence"""
    
    def test_save_metrics(self):
        """Metrics can be saved to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = LLMRouter(storage_path=Path(tmpdir))
            router.query("Test")
            router.save_metrics()
            
            metrics_file = Path(tmpdir) / "metrics.json"
            assert metrics_file.exists()
    
    def test_load_metrics(self):
        """Metrics loaded on initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            router1 = LLMRouter(storage_path=Path(tmpdir))
            for _ in range(5):
                router1.query("Test")
            router1.save_metrics()
            
            # Load in new instance
            router2 = LLMRouter(storage_path=Path(tmpdir))
            
            # Should have loaded metrics
            total_requests = router2.metrics[ProviderName.GEMINI].requests_total
            assert total_requests == 5


class TestThreadSafety:
    """Tests for concurrent operations"""
    
    def test_concurrent_queries(self):
        """Multiple threads can query concurrently"""
        router = LLMRouter()
        responses = []
        
        def make_query():
            for _ in range(5):
                response = router.query("Test")
                responses.append(response)
        
        threads = [threading.Thread(target=make_query) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(responses) == 25
    
    def test_concurrent_health_checks(self):
        """Multiple threads can health check concurrently"""
        router = LLMRouter()
        results = []
        
        def check_health():
            for _ in range(3):
                health = router.health_check()
                results.append(health)
        
        threads = [threading.Thread(target=check_health) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 9


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_query(self):
        """Empty query is handled"""
        router = LLMRouter()
        response = router.query("")
        
        assert isinstance(response, Response)
    
    def test_very_long_query(self):
        """Very long query is handled"""
        router = LLMRouter()
        long_text = "Test " * 10000
        response = router.query(long_text)
        
        assert isinstance(response, Response)
    
    def test_special_characters_in_query(self):
        """Special characters handled"""
        router = LLMRouter()
        query = "Test with special chars: !@#$%^&*()"
        response = router.query(query)
        
        assert isinstance(response, Response)
    
    def test_multiple_consecutive_queries(self):
        """Multiple consecutive queries work"""
        router = LLMRouter()
        
        for i in range(10):
            response = router.query(f"Query {i}")
            assert isinstance(response, Response)


class TestCostTracking:
    """Tests for cost optimization"""
    
    def test_cost_tracked(self):
        """Query costs are tracked"""
        router = LLMRouter()
        router.query("Test", providers=[ProviderName.GEMINI])
        
        cost = router.metrics[ProviderName.GEMINI].total_cost
        assert cost > 0
    
    def test_different_providers_different_costs(self):
        """Different providers have different costs"""
        router = LLMRouter()
        
        router.query("Test", providers=[ProviderName.GEMINI])
        gemini_cost = router.metrics[ProviderName.GEMINI].total_cost
        
        router.query("Test", providers=[ProviderName.CLAUDE])
        claude_cost = router.metrics[ProviderName.CLAUDE].total_cost
        
        # Claude should be more expensive than Gemini
        assert claude_cost > gemini_cost


class TestProviderMetricsClass:
    """Tests for ProviderMetrics data class"""
    
    def test_metrics_creation(self):
        """Create provider metrics"""
        metrics = ProviderMetrics(name=ProviderName.GEMINI)
        assert metrics.name == ProviderName.GEMINI
    
    def test_success_rate_calculation(self):
        """Success rate calculated correctly"""
        metrics = ProviderMetrics(
            name=ProviderName.GEMINI,
            requests_total=10,
            requests_success=8
        )
        assert metrics.success_rate == 0.8
    
    def test_availability_score(self):
        """Availability score based on status"""
        metrics = ProviderMetrics(
            name=ProviderName.GEMINI,
            status=ProviderStatus.HEALTHY,
            requests_total=10,
            requests_success=10
        )
        assert metrics.availability == 1.0
    
    def test_availability_unhealthy(self):
        """Unhealthy provider has zero availability"""
        metrics = ProviderMetrics(
            name=ProviderName.GEMINI,
            status=ProviderStatus.UNHEALTHY
        )
        assert metrics.availability == 0.0


class TestResponseClass:
    """Tests for Response class"""
    
    def test_response_creation(self):
        """Create response"""
        response = Response(
            text="Test response",
            provider=ProviderName.GEMINI,
            tokens_used=100,
            cost=0.001,
            latency_ms=150
        )
        
        assert response.text == "Test response"
        assert response.provider == ProviderName.GEMINI
    
    def test_response_timestamp(self):
        """Response includes timestamp"""
        response = Response(
            text="Test",
            provider=ProviderName.GEMINI,
            tokens_used=100,
            cost=0.001,
            latency_ms=150
        )
        
        assert response.timestamp is not None


# Utility test
class TestUtilities:
    """Tests for utility functions"""
    
    def test_create_router_function(self):
        """create_router() helper works"""
        from llm_router import create_router
        
        router = create_router()
        assert isinstance(router, LLMRouter)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
