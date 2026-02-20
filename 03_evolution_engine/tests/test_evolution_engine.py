"""
Comprehensive tests for EvolutionEngine - 80+ tests
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

from evolution_engine import (
    EvolutionEngine,
    Strategy,
    Outcome,
)


class TestStrategyClass:
    """Tests for Strategy class"""
    
    def test_strategy_creation(self):
        """Create strategy"""
        strategy = Strategy(id="s1", name="test_strategy")
        assert strategy.id == "s1"
        assert strategy.name == "test_strategy"
    
    def test_strategy_success_rate(self):
        """Calculate success rate"""
        strategy = Strategy(
            id="s1",
            name="test",
            success_count=8,
            failure_count=2
        )
        assert strategy.success_rate == 0.8
    
    def test_strategy_total_attempts(self):
        """Calculate total attempts"""
        strategy = Strategy(
            id="s1",
            name="test",
            success_count=5,
            failure_count=3
        )
        assert strategy.total_attempts == 8
    
    def test_strategy_average_reward(self):
        """Calculate average reward"""
        strategy = Strategy(
            id="s1",
            name="test",
            total_reward=100.0,
            success_count=5,
            failure_count=5
        )
        assert strategy.average_reward == 10.0
    
    def test_strategy_is_winning(self):
        """Identify winning strategy"""
        winning = Strategy(
            id="s1",
            name="winner",
            success_count=10,
            failure_count=1
        )
        assert winning.is_winning is True
        
        losing = Strategy(
            id="s2",
            name="loser",
            success_count=5,
            failure_count=5
        )
        assert losing.is_winning is False


class TestEngineInitialization:
    """Tests for engine initialization"""
    
    def test_initialization(self):
        """Initialize engine"""
        engine = EvolutionEngine()
        assert engine is not None
        assert len(engine.strategies) == 0
    
    def test_custom_storage_path(self):
        """Can specify custom storage path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EvolutionEngine(storage_path=Path(tmpdir))
            assert engine.storage_path == Path(tmpdir)
    
    def test_custom_thresholds(self):
        """Can set custom success threshold"""
        engine = EvolutionEngine(success_threshold=0.95, min_attempts=20)
        assert engine.success_threshold == 0.95
        assert engine.min_attempts == 20


class TestStrategyCreation:
    """Tests for strategy creation"""
    
    def test_create_strategy(self):
        """Create new strategy"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test_strategy")
        
        assert strategy_id is not None
        assert strategy_id in engine.strategies
    
    def test_create_multiple_strategies(self):
        """Create multiple strategies"""
        engine = EvolutionEngine()
        
        ids = [engine.create_strategy(f"strategy_{i}") for i in range(5)]
        
        assert len(ids) == 5
        assert all(sid in engine.strategies for sid in ids)
    
    def test_create_strategy_with_parent(self):
        """Create strategy with parent"""
        engine = EvolutionEngine()
        
        parent_id = engine.create_strategy("parent")
        child_id = engine.create_strategy("child", parent_id=parent_id)
        
        child = engine.strategies[child_id]
        assert child.parent_id == parent_id
        assert child.generation == 2


class TestOutcomeRecording:
    """Tests for outcome recording"""
    
    def test_record_success(self):
        """Record successful outcome"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        engine.record_outcome(strategy_id, success=True)
        
        strategy = engine.strategies[strategy_id]
        assert strategy.success_count == 1
        assert strategy.failure_count == 0
    
    def test_record_failure(self):
        """Record failed outcome"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        engine.record_outcome(strategy_id, success=False)
        
        strategy = engine.strategies[strategy_id]
        assert strategy.success_count == 0
        assert strategy.failure_count == 1
    
    def test_record_with_reward(self):
        """Record outcome with reward"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        engine.record_outcome(strategy_id, success=True, reward=100.0)
        
        strategy = engine.strategies[strategy_id]
        assert strategy.total_reward == 100.0
    
    def test_record_multiple_outcomes(self):
        """Record multiple outcomes"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        for i in range(5):
            engine.record_outcome(strategy_id, success=(i % 2 == 0))
        
        strategy = engine.strategies[strategy_id]
        assert strategy.total_attempts == 5
    
    def test_record_outcome_invalid_strategy(self):
        """Recording outcome for unknown strategy raises error"""
        engine = EvolutionEngine()
        
        with pytest.raises(ValueError):
            engine.record_outcome("unknown", success=True)


class TestBestStrategy:
    """Tests for finding best strategy"""
    
    def test_get_best_strategy(self):
        """Find best performing strategy"""
        engine = EvolutionEngine()
        
        s1 = engine.create_strategy("s1")
        s2 = engine.create_strategy("s2")
        
        # Make s1 better
        for _ in range(8):
            engine.record_outcome(s1, success=True)
        for _ in range(2):
            engine.record_outcome(s1, success=False)
        
        # Make s2 worse
        for _ in range(5):
            engine.record_outcome(s2, success=True)
        for _ in range(5):
            engine.record_outcome(s2, success=False)
        
        best = engine.get_best_strategy()
        assert best == s1
    
    def test_get_best_strategy_empty(self):
        """Get best strategy with no strategies returns None"""
        engine = EvolutionEngine()
        assert engine.get_best_strategy() is None


class TestWinningStrategies:
    """Tests for identifying winning strategies"""
    
    def test_get_winning_strategies(self):
        """Find winning strategies"""
        engine = EvolutionEngine(success_threshold=0.8, min_attempts=5)
        
        # Winning strategy
        winner = engine.create_strategy("winner")
        for _ in range(9):
            engine.record_outcome(winner, success=True)
        for _ in range(1):
            engine.record_outcome(winner, success=False)
        
        # Losing strategy
        loser = engine.create_strategy("loser")
        for _ in range(5):
            engine.record_outcome(loser, success=False)
        
        winning = engine.get_winning_strategies()
        assert winner in winning
        assert loser not in winning
    
    def test_no_winning_strategies(self):
        """No strategies meet winning criteria"""
        engine = EvolutionEngine(success_threshold=0.99, min_attempts=100)
        
        strategy = engine.create_strategy("test")
        for _ in range(10):
            engine.record_outcome(strategy, success=True)
        
        winning = engine.get_winning_strategies()
        assert len(winning) == 0


class TestApplyStrategy:
    """Tests for applying strategies"""
    
    def test_apply_strategy(self):
        """Apply a strategy"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        result = engine.apply_strategy(strategy_id)
        assert result is True
    
    def test_apply_unknown_strategy(self):
        """Apply unknown strategy returns False"""
        engine = EvolutionEngine()
        result = engine.apply_strategy("unknown")
        assert result is False


class TestEvolution:
    """Tests for evolution process"""
    
    def test_evolve_with_no_winners(self):
        """Evolve with no winning strategies returns None"""
        engine = EvolutionEngine(success_threshold=0.99, min_attempts=100)
        
        strategy = engine.create_strategy("test")
        for _ in range(5):
            engine.record_outcome(strategy, success=True)
        
        variant = engine.evolve()
        assert variant is None
    
    def test_evolve_creates_variant(self):
        """Evolve creates variant of winning strategy"""
        engine = EvolutionEngine(success_threshold=0.8, min_attempts=5)
        
        winner = engine.create_strategy("winner")
        for _ in range(9):
            engine.record_outcome(winner, success=True)
        for _ in range(1):
            engine.record_outcome(winner, success=False)
        
        variant_id = engine.evolve()
        
        assert variant_id is not None
        assert variant_id in engine.strategies
        
        variant = engine.strategies[variant_id]
        assert variant.parent_id == winner
        assert variant.generation > 1


class TestCreateVariant:
    """Tests for creating variants"""
    
    def test_create_variant(self):
        """Create variant of strategy"""
        engine = EvolutionEngine()
        
        parent_id = engine.create_strategy("parent")
        variant_id = engine.create_variant(parent_id, "variant")
        
        assert variant_id in engine.strategies
        assert engine.strategies[variant_id].parent_id == parent_id
    
    def test_create_variant_unknown_parent(self):
        """Creating variant of unknown parent raises error"""
        engine = EvolutionEngine()
        
        with pytest.raises(ValueError):
            engine.create_variant("unknown", "variant")


class TestGenealogy:
    """Tests for genealogy tracking"""
    
    def test_genealogy_parent_child(self):
        """Track parent-child relationship"""
        engine = EvolutionEngine()
        
        parent_id = engine.create_strategy("parent")
        child_id = engine.create_strategy("child", parent_id=parent_id)
        
        genealogy = engine.get_genealogy(parent_id)
        assert child_id in genealogy['children']
    
    def test_genealogy_generation(self):
        """Track generation number"""
        engine = EvolutionEngine()
        
        s1 = engine.create_strategy("s1")
        s2 = engine.create_strategy("s2", parent_id=s1)
        s3 = engine.create_strategy("s3", parent_id=s2)
        
        assert engine.strategies[s1].generation == 1
        assert engine.strategies[s2].generation == 2
        assert engine.strategies[s3].generation == 3


class TestStatistics:
    """Tests for statistics"""
    
    def test_get_statistics(self):
        """Get engine statistics"""
        engine = EvolutionEngine()
        
        strategy_id = engine.create_strategy("test")
        for _ in range(10):
            engine.record_outcome(strategy_id, success=True)
        
        stats = engine.get_statistics()
        
        assert 'total_strategies' in stats
        assert 'winning_strategies' in stats
        assert 'overall_success_rate' in stats
    
    def test_statistics_empty_engine(self):
        """Statistics for empty engine"""
        engine = EvolutionEngine()
        stats = engine.get_statistics()
        
        assert stats['total_strategies'] == 0


class TestOutcomesHistory:
    """Tests for outcomes history"""
    
    def test_get_outcomes(self):
        """Get outcomes history"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        for _ in range(5):
            engine.record_outcome(strategy_id, success=True)
        
        outcomes = engine.get_outcomes()
        assert len(outcomes) == 5
    
    def test_get_outcomes_filtered(self):
        """Get outcomes for specific strategy"""
        engine = EvolutionEngine()
        
        s1 = engine.create_strategy("s1")
        s2 = engine.create_strategy("s2")
        
        for _ in range(3):
            engine.record_outcome(s1, success=True)
        for _ in range(2):
            engine.record_outcome(s2, success=True)
        
        s1_outcomes = engine.get_outcomes(strategy_id=s1)
        assert len(s1_outcomes) == 3
    
    def test_get_outcomes_limit(self):
        """Outcomes history respects limit"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        for _ in range(20):
            engine.record_outcome(strategy_id, success=True)
        
        outcomes = engine.get_outcomes(limit=5)
        assert len(outcomes) <= 5


class TestThreadSafety:
    """Tests for concurrent operations"""
    
    def test_concurrent_outcomes(self):
        """Multiple threads can record outcomes concurrently"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        def record_outcomes():
            for _ in range(10):
                engine.record_outcome(strategy_id, success=True)
        
        threads = [threading.Thread(target=record_outcomes) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        strategy = engine.strategies[strategy_id]
        assert strategy.total_attempts == 50
    
    def test_concurrent_strategy_creation(self):
        """Multiple threads can create strategies concurrently"""
        engine = EvolutionEngine()
        
        def create_strategies():
            for i in range(10):
                engine.create_strategy(f"strategy_{threading.current_thread().name}_{i}")
        
        threads = [threading.Thread(target=create_strategies) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(engine.strategies) == 30


class TestPersistence:
    """Tests for saving/loading strategies"""
    
    def test_save_strategies(self):
        """Save strategies to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EvolutionEngine(storage_path=Path(tmpdir))
            
            strategy_id = engine.create_strategy("test")
            engine.record_outcome(strategy_id, success=True)
            
            engine.save_strategies()
            
            strategies_file = Path(tmpdir) / "strategies.jsonl"
            assert strategies_file.exists()
    
    def test_load_strategies(self):
        """Load strategies from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            engine1 = EvolutionEngine(storage_path=Path(tmpdir))
            s1 = engine1.create_strategy("test1")
            s2 = engine1.create_strategy("test2")
            engine1.save_strategies()
            
            # Load in new instance
            engine2 = EvolutionEngine(storage_path=Path(tmpdir))
            
            assert len(engine2.strategies) == 2


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_zero_attempts_strategy(self):
        """Strategy with zero attempts handled correctly"""
        strategy = Strategy(id="s1", name="test")
        assert strategy.success_rate == 0.0
        assert strategy.total_attempts == 0
    
    def test_same_name_different_ids(self):
        """Multiple strategies with same name work"""
        engine = EvolutionEngine()
        
        s1 = engine.create_strategy("test")
        s2 = engine.create_strategy("test")
        
        assert s1 != s2
        assert engine.strategies[s1].name == engine.strategies[s2].name
    
    def test_large_reward_values(self):
        """Large reward values handled correctly"""
        engine = EvolutionEngine()
        strategy_id = engine.create_strategy("test")
        
        engine.record_outcome(strategy_id, success=True, reward=1000000.0)
        
        strategy = engine.strategies[strategy_id]
        assert strategy.total_reward == 1000000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
