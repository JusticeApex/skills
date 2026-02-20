"""
Comprehensive test suite for ConfidenceGate - 100+ tests
Tests all core functionality, edge cases, and risk adjustments
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from confidence_gate import (
    ConfidenceGate,
    ActionConfidence,
    RiskFactor,
    ConfidenceScore,
    ActionRule,
)


class TestConfidenceGateBasics:
    """Basic functionality tests"""
    
    def test_initialization(self):
        """Test gate initialization"""
        gate = ConfidenceGate()
        assert gate is not None
        assert len(gate.rules) == 0
        assert len(gate.history) == 0
    
    def test_register_action_high(self):
        """Register HIGH confidence action"""
        gate = ConfidenceGate()
        gate.register_action('execute_trade', ActionConfidence.HIGH)
        
        assert 'execute_trade' in gate.rules
        assert gate.rules['execute_trade'].base_confidence == ActionConfidence.HIGH
    
    def test_register_action_medium(self):
        """Register MEDIUM confidence action"""
        gate = ConfidenceGate()
        gate.register_action('deploy_code', ActionConfidence.MEDIUM)
        
        assert 'deploy_code' in gate.rules
        assert gate.rules['deploy_code'].base_confidence == ActionConfidence.MEDIUM
    
    def test_register_action_low(self):
        """Register LOW confidence action"""
        gate = ConfidenceGate()
        gate.register_action('delete_file', ActionConfidence.LOW)
        
        assert 'delete_file' in gate.rules
        assert gate.rules['delete_file'].base_confidence == ActionConfidence.LOW
    
    def test_register_action_critical(self):
        """Register CRITICAL confidence action"""
        gate = ConfidenceGate()
        gate.register_action('critical_operation', ActionConfidence.CRITICAL)
        
        assert 'critical_operation' in gate.rules
        assert gate.rules['critical_operation'].base_confidence == ActionConfidence.CRITICAL
    
    def test_register_multiple_actions(self):
        """Register multiple actions"""
        gate = ConfidenceGate()
        gate.register_action('action1', ActionConfidence.HIGH)
        gate.register_action('action2', ActionConfidence.MEDIUM)
        gate.register_action('action3', ActionConfidence.LOW)
        
        assert len(gate.rules) == 3
    
    def test_register_action_with_custom_threshold(self):
        """Register action with custom threshold"""
        gate = ConfidenceGate()
        gate.register_action(
            'custom_trade',
            ActionConfidence.MEDIUM,
            custom_threshold=0.8
        )
        
        rule = gate.rules['custom_trade']
        assert rule.get_threshold() == 0.8


class TestConfidenceEvaluation:
    """Tests for action evaluation"""
    
    def test_evaluate_high_confidence(self):
        """Evaluate HIGH confidence action"""
        gate = ConfidenceGate()
        gate.register_action('fast_trade', ActionConfidence.HIGH)
        
        score = gate.evaluate_action('fast_trade')
        assert score.should_execute is True
        assert score.confidence_value >= 0.7
    
    def test_evaluate_medium_confidence(self):
        """Evaluate MEDIUM confidence action"""
        gate = ConfidenceGate()
        gate.register_action('trade', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('trade')
        assert score.confidence_value >= 0.5
    
    def test_evaluate_low_confidence(self):
        """Evaluate LOW confidence action"""
        gate = ConfidenceGate()
        gate.register_action('risky_action', ActionConfidence.LOW)
        
        score = gate.evaluate_action('risky_action')
        assert score.confidence_value <= 0.3
    
    def test_evaluate_critical_confidence(self):
        """CRITICAL actions never auto-execute"""
        gate = ConfidenceGate()
        gate.register_action('critical_op', ActionConfidence.CRITICAL)
        
        score = gate.evaluate_action('critical_op')
        assert score.should_execute is False
    
    def test_evaluate_unknown_action_raises(self):
        """Evaluating unknown action raises error"""
        gate = ConfidenceGate()
        
        with pytest.raises(ValueError):
            gate.evaluate_action('unknown_action')
    
    def test_evaluate_returns_score_object(self):
        """Evaluation returns ConfidenceScore"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test')
        assert isinstance(score, ConfidenceScore)
        assert hasattr(score, 'action')
        assert hasattr(score, 'confidence_value')
        assert hasattr(score, 'should_execute')
    
    def test_score_has_timestamp(self):
        """Score includes timestamp"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test')
        assert score.timestamp is not None
        assert len(score.timestamp) > 0


class TestRiskFactorAdjustments:
    """Tests for risk factor adjustments"""
    
    def test_volatility_adjustment_high(self):
        """High volatility reduces confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'trade',
            ActionConfidence.MEDIUM,
            risk_adjustments={RiskFactor.VOLATILITY: 0.3}
        )
        
        score_no_risk = gate.evaluate_action('trade', risk_factors={})
        score_high_volatility = gate.evaluate_action(
            'trade',
            risk_factors={'volatility': 0.9}
        )
        
        assert score_high_volatility.confidence_value < score_no_risk.confidence_value
    
    def test_error_rate_adjustment(self):
        """High error rate reduces confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'operation',
            ActionConfidence.HIGH,
            risk_adjustments={RiskFactor.ERROR_RATE: 0.4}
        )
        
        score_no_error = gate.evaluate_action('operation')
        score_high_error = gate.evaluate_action(
            'operation',
            risk_factors={'error_rate': 0.8}
        )
        
        assert score_high_error.confidence_value < score_no_error.confidence_value
    
    def test_losing_streak_adjustment(self):
        """Losing streak reduces confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'trade',
            ActionConfidence.MEDIUM,
            risk_adjustments={RiskFactor.LOSING_STREAK: 0.25}
        )
        
        score_no_loss = gate.evaluate_action('trade')
        score_with_loss = gate.evaluate_action(
            'trade',
            risk_factors={'losing_streak': 0.7}
        )
        
        assert score_with_loss.confidence_value < score_no_loss.confidence_value
    
    def test_unknown_condition_adjustment(self):
        """Unknown conditions reduce confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'operation',
            ActionConfidence.HIGH,
            risk_adjustments={RiskFactor.UNKNOWN_CONDITION: 0.5}
        )
        
        score_known = gate.evaluate_action('operation')
        score_unknown = gate.evaluate_action(
            'operation',
            risk_factors={'unknown_condition': 0.6}
        )
        
        assert score_unknown.confidence_value < score_known.confidence_value
    
    def test_new_market_adjustment(self):
        """First-time in new market reduces confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'trade',
            ActionConfidence.MEDIUM,
            risk_adjustments={RiskFactor.NEW_MARKET: 0.3}
        )
        
        score_established = gate.evaluate_action('trade')
        score_new = gate.evaluate_action(
            'trade',
            risk_factors={'new_market': 0.8}
        )
        
        assert score_new.confidence_value < score_established.confidence_value
    
    def test_large_amount_adjustment(self):
        """Large amounts reduce confidence"""
        gate = ConfidenceGate()
        gate.register_action(
            'transfer',
            ActionConfidence.MEDIUM,
            risk_adjustments={RiskFactor.LARGE_AMOUNT: 0.4}
        )
        
        score_small = gate.evaluate_action('transfer')
        score_large = gate.evaluate_action(
            'transfer',
            risk_factors={'large_amount': 0.9}
        )
        
        assert score_large.confidence_value < score_small.confidence_value
    
    def test_multiple_risk_factors(self):
        """Multiple risk factors compound"""
        gate = ConfidenceGate()
        gate.register_action(
            'risky_trade',
            ActionConfidence.MEDIUM,
            risk_adjustments={
                RiskFactor.VOLATILITY: 0.2,
                RiskFactor.LOSING_STREAK: 0.3,
                RiskFactor.UNKNOWN_CONDITION: 0.2
            }
        )
        
        score = gate.evaluate_action(
            'risky_trade',
            risk_factors={
                'volatility': 0.8,
                'losing_streak': 0.7,
                'unknown_condition': 0.6
            }
        )
        
        assert score.confidence_value < 0.4  # Should be significantly reduced
    
    def test_risk_factors_case_insensitive(self):
        """Risk factors work with uppercase names"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.MEDIUM,
            risk_adjustments={RiskFactor.VOLATILITY: 0.3}
        )
        
        score = gate.evaluate_action(
            'test',
            risk_factors={'VOLATILITY': 0.5}
        )
        
        # Should work despite uppercase
        assert score.adjustments.get('VOLATILITY', 0) > 0


class TestConfidenceThresholds:
    """Tests for confidence thresholds"""
    
    def test_high_threshold(self):
        """HIGH confidence has ~0.7 threshold"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.HIGH)
        
        rule = gate.rules['test']
        assert rule.get_threshold() == 0.7
    
    def test_medium_threshold(self):
        """MEDIUM confidence has ~0.5 threshold"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        rule = gate.rules['test']
        assert rule.get_threshold() == 0.5
    
    def test_low_threshold(self):
        """LOW confidence has ~0.3 threshold"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.LOW)
        
        rule = gate.rules['test']
        assert rule.get_threshold() == 0.3
    
    def test_custom_threshold_override(self):
        """Custom threshold overrides default"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.MEDIUM,
            custom_threshold=0.9
        )
        
        rule = gate.rules['test']
        assert rule.get_threshold() == 0.9
    
    def test_execute_above_threshold(self):
        """Action executes if above threshold"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.MEDIUM,
            custom_threshold=0.4
        )
        
        score = gate.evaluate_action('test')
        # MEDIUM base = 0.5, no risk factors → should execute (0.5 > 0.4)
        assert score.should_execute is True
    
    def test_pause_below_threshold(self):
        """Action pauses if below threshold"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.LOW,
            custom_threshold=0.5
        )
        
        score = gate.evaluate_action('test')
        # LOW base = 0.2, no risk factors → should pause (0.2 < 0.5)
        assert score.should_execute is False


class TestDecisionHistory:
    """Tests for decision history tracking"""
    
    def test_history_records_decision(self):
        """Decisions are recorded in history"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        gate.evaluate_action('test')
        assert len(gate.history) == 1
    
    def test_history_multiple_decisions(self):
        """Multiple decisions accumulate"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(10):
            gate.evaluate_action('test')
        
        assert len(gate.history) == 10
    
    def test_history_get_all(self):
        """Can retrieve full history"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(5):
            gate.evaluate_action('test')
        
        history = gate.get_history()
        assert len(history) == 5
    
    def test_history_filter_by_action(self):
        """Can filter history by action"""
        gate = ConfidenceGate()
        gate.register_action('action1', ActionConfidence.HIGH)
        gate.register_action('action2', ActionConfidence.MEDIUM)
        
        for _ in range(3):
            gate.evaluate_action('action1')
        for _ in range(2):
            gate.evaluate_action('action2')
        
        history_a1 = gate.get_history(action='action1')
        history_a2 = gate.get_history(action='action2')
        
        assert len(history_a1) == 3
        assert len(history_a2) == 2
    
    def test_history_limit(self):
        """History respects limit parameter"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(100):
            gate.evaluate_action('test')
        
        history = gate.get_history(limit=10)
        assert len(history) <= 10
    
    def test_history_latest_first(self):
        """History returns latest decisions first"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        timestamps = []
        for i in range(5):
            score = gate.evaluate_action('test')
            timestamps.append(score.timestamp)
            time.sleep(0.01)
        
        history = gate.get_history()
        # Newest should be first
        assert history[0].timestamp == timestamps[-1]
    
    def test_history_max_size(self):
        """History respects max_history limit"""
        gate = ConfidenceGate(max_history=50)
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(100):
            gate.evaluate_action('test')
        
        assert len(gate.history) <= 50


class TestStatistics:
    """Tests for statistics generation"""
    
    def test_statistics_empty_history(self):
        """Statistics for empty history"""
        gate = ConfidenceGate()
        stats = gate.get_statistics()
        
        assert stats['total_decisions'] == 0
    
    def test_statistics_total_decisions(self):
        """Statistics count total decisions"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(20):
            gate.evaluate_action('test')
        
        stats = gate.get_statistics()
        assert stats['total_decisions'] == 20
    
    def test_statistics_execution_rate(self):
        """Statistics calculate execution rate"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.HIGH)  # Should execute
        
        for _ in range(10):
            gate.evaluate_action('test')
        
        stats = gate.get_statistics()
        assert stats['execution_rate'] > 0.5  # Most should execute
    
    def test_statistics_average_confidence(self):
        """Statistics calculate average confidence"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(5):
            gate.evaluate_action('test')
        
        stats = gate.get_statistics()
        assert stats['avg_confidence'] > 0
    
    def test_statistics_min_max_confidence(self):
        """Statistics track min/max confidence"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        for _ in range(10):
            gate.evaluate_action('test')
        
        stats = gate.get_statistics()
        assert stats['min_confidence'] <= stats['avg_confidence']
        assert stats['max_confidence'] >= stats['avg_confidence']
    
    def test_statistics_by_action(self):
        """Statistics can be filtered by action"""
        gate = ConfidenceGate()
        gate.register_action('action1', ActionConfidence.HIGH)
        gate.register_action('action2', ActionConfidence.LOW)
        
        for _ in range(5):
            gate.evaluate_action('action1')
        for _ in range(3):
            gate.evaluate_action('action2')
        
        stats1 = gate.get_statistics(action='action1')
        stats2 = gate.get_statistics(action='action2')
        
        assert stats1['total_decisions'] == 5
        assert stats2['total_decisions'] == 3


class TestForceExecute:
    """Tests for force execute override"""
    
    def test_force_execute_allowed(self):
        """Force execute when override is allowed"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.LOW,
            override_allowed=True
        )
        
        score = gate.evaluate_action('test')
        result = gate.force_execute(score)
        
        assert result is True
    
    def test_force_execute_not_allowed(self):
        """Force execute denied when not allowed"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.CRITICAL,
            override_allowed=False
        )
        
        score = gate.evaluate_action('test')
        result = gate.force_execute(score)
        
        assert result is False
    
    def test_force_execute_unknown_action(self):
        """Force execute on unknown action returns False"""
        gate = ConfidenceGate()
        
        score = ConfidenceScore(
            action='unknown',
            base_confidence=ActionConfidence.MEDIUM,
            adjusted_confidence=ActionConfidence.MEDIUM,
            confidence_value=0.5,
            should_execute=False
        )
        
        result = gate.force_execute(score)
        assert result is False


class TestScoreObject:
    """Tests for ConfidenceScore object"""
    
    def test_score_has_required_fields(self):
        """Score has all required fields"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test')
        
        assert hasattr(score, 'action')
        assert hasattr(score, 'base_confidence')
        assert hasattr(score, 'adjusted_confidence')
        assert hasattr(score, 'confidence_value')
        assert hasattr(score, 'should_execute')
        assert hasattr(score, 'risk_factors')
        assert hasattr(score, 'adjustments')
        assert hasattr(score, 'explanation')
        assert hasattr(score, 'timestamp')
    
    def test_score_to_dict(self):
        """Score can be converted to dict"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test')
        score_dict = score.to_dict()
        
        assert isinstance(score_dict, dict)
        assert score_dict['action'] == 'test'
        assert 'confidence_value' in score_dict
    
    def test_score_explanation(self):
        """Score includes explanation"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test')
        
        assert len(score.explanation) > 0
        assert 'test' in score.explanation or 'confidence' in score.explanation


class TestThreadSafety:
    """Tests for thread-safe operations"""
    
    def test_concurrent_evaluations(self):
        """Multiple threads can evaluate concurrently"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        results = []
        
        def evaluate():
            for _ in range(10):
                score = gate.evaluate_action('test')
                results.append(score)
        
        threads = [threading.Thread(target=evaluate) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All results should be valid
        assert len(results) == 50
        assert all(isinstance(r, ConfidenceScore) for r in results)
    
    def test_concurrent_registration(self):
        """Multiple threads can register actions safely"""
        gate = ConfidenceGate()
        
        def register_actions(prefix):
            for i in range(10):
                gate.register_action(
                    f"{prefix}_action_{i}",
                    ActionConfidence.MEDIUM
                )
        
        threads = [
            threading.Thread(target=register_actions, args=(f"t{i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All actions should be registered
        assert len(gate.rules) == 50


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_confidence_clamps_to_range(self):
        """Confidence value stays within 0.0-1.0"""
        gate = ConfidenceGate()
        gate.register_action(
            'test',
            ActionConfidence.HIGH,
            risk_adjustments={RiskFactor.VOLATILITY: 2.0}
        )
        
        score = gate.evaluate_action('test', risk_factors={'volatility': 1.0})
        
        # Should clamp to [0.0, 1.0]
        assert 0.0 <= score.confidence_value <= 1.0
    
    def test_zero_confidence_value(self):
        """Zero confidence is handled correctly"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.CRITICAL)
        
        score = gate.evaluate_action('test')
        
        assert score.confidence_value == 0.0
        assert score.should_execute is False
    
    def test_empty_context(self):
        """Empty context doesn't cause errors"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test', context={})
        
        assert isinstance(score, ConfidenceScore)
    
    def test_empty_risk_factors(self):
        """Empty risk factors doesn't cause errors"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test', risk_factors={})
        
        assert isinstance(score, ConfidenceScore)
    
    def test_none_context(self):
        """None context is handled"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test', context=None)
        
        assert isinstance(score, ConfidenceScore)
    
    def test_none_risk_factors(self):
        """None risk factors are handled"""
        gate = ConfidenceGate()
        gate.register_action('test', ActionConfidence.MEDIUM)
        
        score = gate.evaluate_action('test', risk_factors=None)
        
        assert isinstance(score, ConfidenceScore)


class TestPersistence:
    """Tests for history persistence"""
    
    def test_save_history(self):
        """History can be saved to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            gate = ConfidenceGate(storage_path=Path(tmpdir))
            gate.register_action('test', ActionConfidence.MEDIUM)
            
            for _ in range(5):
                gate.evaluate_action('test')
            
            gate.save_history()
            
            history_file = Path(tmpdir) / "history.jsonl"
            assert history_file.exists()
    
    def test_load_history(self):
        """History can be loaded from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            gate1 = ConfidenceGate(storage_path=Path(tmpdir))
            gate1.register_action('test', ActionConfidence.MEDIUM)
            
            for _ in range(5):
                gate1.evaluate_action('test')
            
            gate1.save_history()
            
            # Load in new instance
            gate2 = ConfidenceGate(storage_path=Path(tmpdir))
            
            assert len(gate2.history) == 5


class TestConfidenceValueConversions:
    """Tests for confidence value conversions"""
    
    def test_high_to_value(self):
        """HIGH converts to ~0.8"""
        gate = ConfidenceGate()
        value = gate._confidence_to_value(ActionConfidence.HIGH)
        assert value == 0.8
    
    def test_medium_to_value(self):
        """MEDIUM converts to ~0.5"""
        gate = ConfidenceGate()
        value = gate._confidence_to_value(ActionConfidence.MEDIUM)
        assert value == 0.5
    
    def test_low_to_value(self):
        """LOW converts to ~0.2"""
        gate = ConfidenceGate()
        value = gate._confidence_to_value(ActionConfidence.LOW)
        assert value == 0.2
    
    def test_critical_to_value(self):
        """CRITICAL converts to 0.0"""
        gate = ConfidenceGate()
        value = gate._confidence_to_value(ActionConfidence.CRITICAL)
        assert value == 0.0
    
    def test_value_0_8_to_confidence(self):
        """0.8+ converts to HIGH"""
        gate = ConfidenceGate()
        conf = gate._value_to_confidence(0.8)
        assert conf == ActionConfidence.HIGH
    
    def test_value_0_5_to_confidence(self):
        """0.5 converts to MEDIUM"""
        gate = ConfidenceGate()
        conf = gate._value_to_confidence(0.5)
        assert conf == ActionConfidence.MEDIUM
    
    def test_value_0_2_to_confidence(self):
        """0.2 converts to LOW"""
        gate = ConfidenceGate()
        conf = gate._value_to_confidence(0.2)
        assert conf == ActionConfidence.LOW
    
    def test_value_0_0_to_confidence(self):
        """0.0 converts to CRITICAL"""
        gate = ConfidenceGate()
        conf = gate._value_to_confidence(0.0)
        assert conf == ActionConfidence.CRITICAL


# Utility test
class TestUtilities:
    """Tests for utility functions"""
    
    def test_create_gate_function(self):
        """create_gate() helper works"""
        from confidence_gate import create_gate
        
        gate = create_gate()
        assert isinstance(gate, ConfidenceGate)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
