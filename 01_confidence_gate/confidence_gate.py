"""
CONFIDENCE GATE - Quality Control System
=========================================

Evaluates actions before execution to enable safe automation.
Distinguishes between high-confidence actions (auto-execute) and risky ones (pause for review).

Features:
- 4 confidence levels (HIGH, MEDIUM, LOW, CRITICAL)
- Risk factor adjustments
- Complete decision history
- Custom rules per action type
- Manual override capability

Author: Justice Apex LLC
License: MIT
"""

import threading
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionConfidence(Enum):
    """Confidence levels for actions"""
    HIGH = "high"  # Execute immediately
    MEDIUM = "medium"  # Execute but log
    LOW = "low"  # Pause for review
    CRITICAL = "critical"  # Always pause


class RiskFactor(Enum):
    """Risk factors that affect confidence"""
    VOLATILITY = "volatility"  # Market/system volatility
    ERROR_RATE = "error_rate"  # Recent error frequency
    LOSING_STREAK = "losing_streak"  # Consecutive failures
    UNKNOWN_CONDITION = "unknown_condition"  # Untested condition
    NEW_MARKET = "new_market"  # First time in market/domain
    LARGE_AMOUNT = "large_amount"  # Large transaction size


@dataclass
class ConfidenceScore:
    """Result of confidence evaluation"""
    action: str
    base_confidence: ActionConfidence
    adjusted_confidence: ActionConfidence
    confidence_value: float  # 0.0 to 1.0
    should_execute: bool  # True if >= threshold
    risk_factors: Dict[str, float] = field(default_factory=dict)
    adjustments: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'action': self.action,
            'base_confidence': self.base_confidence.value,
            'adjusted_confidence': self.adjusted_confidence.value,
            'confidence_value': self.confidence_value,
            'should_execute': self.should_execute,
            'risk_factors': self.risk_factors,
            'adjustments': self.adjustments,
            'explanation': self.explanation,
            'timestamp': self.timestamp
        }


@dataclass
class ActionRule:
    """Rule for an action type"""
    action: str
    base_confidence: ActionConfidence
    custom_threshold: Optional[float] = None  # Override default threshold
    risk_adjustments: Dict[RiskFactor, float] = field(default_factory=dict)
    override_allowed: bool = True
    
    def get_threshold(self) -> float:
        """Get execution threshold (0.0 to 1.0)"""
        if self.custom_threshold is not None:
            return self.custom_threshold
        
        # Default thresholds by confidence level
        thresholds = {
            ActionConfidence.HIGH: 0.7,
            ActionConfidence.MEDIUM: 0.5,
            ActionConfidence.LOW: 0.3,
            ActionConfidence.CRITICAL: 0.0  # Always pauses
        }
        return thresholds.get(self.base_confidence, 0.5)


class ConfidenceGate:
    """
    Quality control system that evaluates actions before execution.
    
    Enables safe automation by distinguishing between:
    - HIGH: Auto-execute (>0.7 confidence)
    - MEDIUM: Execute but log (>0.5 confidence)
    - LOW: Pause for review (<0.3 confidence)
    - CRITICAL: Always pause (manual approval required)
    """
    
    def __init__(self, storage_path: Optional[Path] = None, max_history: int = 10000):
        """
        Initialize ConfidenceGate
        
        Args:
            storage_path: Path to store decision history
            max_history: Maximum decisions to keep in memory
        """
        self.storage_path = storage_path or Path("confidence_gate_history")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Action rules registry
        self.rules: Dict[str, ActionRule] = {}
        
        # Decision history (latest first)
        self.history: deque = deque(maxlen=max_history)
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Load history if it exists
        self._load_history()
        
        logger.info(f"ConfidenceGate initialized with {len(self.rules)} rules")
    
    def register_action(
        self,
        action: str,
        confidence: ActionConfidence,
        custom_threshold: Optional[float] = None,
        risk_adjustments: Optional[Dict[RiskFactor, float]] = None
    ):
        """
        Register an action type with confidence level
        
        Args:
            action: Action name (e.g., 'make_trade', 'deploy_code')
            confidence: Base confidence level
            custom_threshold: Override default threshold (0.0-1.0)
            risk_adjustments: How risk factors affect confidence
        """
        with self._lock:
            self.rules[action] = ActionRule(
                action=action,
                base_confidence=confidence,
                custom_threshold=custom_threshold,
                risk_adjustments=risk_adjustments or {}
            )
            logger.info(f"Registered action: {action} with {confidence.value} confidence")
    
    def evaluate_action(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[Dict[str, float]] = None
    ) -> ConfidenceScore:
        """
        Evaluate whether an action should execute
        
        Args:
            action: Action name to evaluate
            context: Action context (amount, target, etc.)
            risk_factors: Current risk factors affecting decision
        
        Returns:
            ConfidenceScore with decision and explanation
        """
        with self._lock:
            if action not in self.rules:
                raise ValueError(f"Unknown action: {action}")
            
            rule = self.rules[action]
            context = context or {}
            risk_factors = risk_factors or {}
            
            # Start with base confidence
            base_conf = rule.base_confidence
            confidence_value = self._confidence_to_value(base_conf)
            
            # Apply risk factor adjustments
            adjustments = {}
            for risk_type, risk_level in risk_factors.items():
                if hasattr(RiskFactor, risk_type.upper()):
                    risk_factor = RiskFactor[risk_type.upper()]
                    adjustment = rule.risk_adjustments.get(risk_factor, 0.0)
                    adjustment *= risk_level  # Scale by risk level (0.0-1.0)
                    confidence_value -= adjustment
                    adjustments[risk_type] = adjustment
            
            # Clamp to valid range
            confidence_value = max(0.0, min(1.0, confidence_value))
            
            # Determine if should execute
            threshold = rule.get_threshold()
            should_execute = confidence_value >= threshold or base_conf == ActionConfidence.HIGH
            
            # Critical actions never auto-execute
            if base_conf == ActionConfidence.CRITICAL:
                should_execute = False
            
            # Create score
            score = ConfidenceScore(
                action=action,
                base_confidence=base_conf,
                adjusted_confidence=self._value_to_confidence(confidence_value),
                confidence_value=confidence_value,
                should_execute=should_execute,
                risk_factors=risk_factors,
                adjustments=adjustments,
                explanation=self._generate_explanation(
                    action, base_conf, confidence_value, threshold, risk_factors
                )
            )
            
            # Store in history
            self.history.appendleft(score)
            
            # Log decision
            log_level = logging.WARNING if not should_execute else logging.INFO
            logger.log(
                log_level,
                f"Action '{action}': confidence={confidence_value:.2f}, "
                f"threshold={threshold:.2f}, execute={should_execute}"
            )
            
            return score
    
    def force_execute(self, score: ConfidenceScore) -> bool:
        """
        Force execute an action that was paused
        
        Args:
            score: The ConfidenceScore to override
        
        Returns:
            True if override was allowed
        """
        with self._lock:
            if score.action not in self.rules:
                return False
            
            rule = self.rules[score.action]
            if not rule.override_allowed:
                logger.warning(f"Override not allowed for action: {score.action}")
                return False
            
            logger.info(f"Force executing action: {score.action}")
            return True
    
    def get_history(
        self,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[ConfidenceScore]:
        """
        Get decision history
        
        Args:
            action: Filter by action type (None = all)
            limit: Maximum number of decisions to return
        
        Returns:
            List of ConfidenceScore objects
        """
        with self._lock:
            results = list(self.history)
            
            if action:
                results = [s for s in results if s.action == action]
            
            return results[:limit]
    
    def get_statistics(self, action: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics on decision history
        
        Args:
            action: Calculate stats for specific action (None = all)
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            history = self.get_history(action=action, limit=1000)
            
            if not history:
                return {"total_decisions": 0}
            
            executed = sum(1 for s in history if s.should_execute)
            paused = len(history) - executed
            avg_confidence = sum(s.confidence_value for s in history) / len(history)
            
            return {
                "total_decisions": len(history),
                "executed": executed,
                "paused": paused,
                "execution_rate": executed / len(history) if history else 0.0,
                "avg_confidence": avg_confidence,
                "min_confidence": min(s.confidence_value for s in history),
                "max_confidence": max(s.confidence_value for s in history)
            }
    
    # Private methods
    
    def _confidence_to_value(self, confidence: ActionConfidence) -> float:
        """Convert confidence level to numeric value"""
        values = {
            ActionConfidence.HIGH: 0.8,
            ActionConfidence.MEDIUM: 0.5,
            ActionConfidence.LOW: 0.2,
            ActionConfidence.CRITICAL: 0.0
        }
        return values.get(confidence, 0.5)
    
    def _value_to_confidence(self, value: float) -> ActionConfidence:
        """Convert numeric value back to confidence level"""
        if value >= 0.7:
            return ActionConfidence.HIGH
        elif value >= 0.4:
            return ActionConfidence.MEDIUM
        elif value >= 0.1:
            return ActionConfidence.LOW
        else:
            return ActionConfidence.CRITICAL
    
    def _generate_explanation(
        self,
        action: str,
        base_conf: ActionConfidence,
        confidence_value: float,
        threshold: float,
        risk_factors: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation"""
        parts = [
            f"Action '{action}' confidence: {confidence_value:.2f}",
            f"Threshold: {threshold:.2f}",
            f"Base: {base_conf.value}"
        ]
        
        if risk_factors:
            parts.append(f"Risk factors: {risk_factors}")
        
        if confidence_value < threshold:
            parts.append("❌ Below threshold - PAUSED FOR REVIEW")
        else:
            parts.append("✅ Above threshold - AUTO-EXECUTE")
        
        return " | ".join(parts)
    
    def _load_history(self):
        """Load decision history from storage"""
        history_file = self.storage_path / "history.jsonl"
        if history_file.exists():
            try:
                count = 0
                for line in history_file.read_text().split('\n'):
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    # Reconstruct ConfidenceScore
                    score = ConfidenceScore(
                        action=data['action'],
                        base_confidence=ActionConfidence(data['base_confidence']),
                        adjusted_confidence=ActionConfidence(data['adjusted_confidence']),
                        confidence_value=data['confidence_value'],
                        should_execute=data['should_execute'],
                        risk_factors=data.get('risk_factors', {}),
                        adjustments=data.get('adjustments', {}),
                        explanation=data.get('explanation', ''),
                        timestamp=data.get('timestamp', '')
                    )
                    self.history.appendleft(score)
                    count += 1
                
                logger.info(f"Loaded {count} decisions from history")
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
    
    def save_history(self):
        """Save decision history to storage"""
        history_file = self.storage_path / "history.jsonl"
        with self._lock:
            try:
                with open(history_file, 'w') as f:
                    for score in self.history:
                        f.write(json.dumps(score.to_dict()) + '\n')
                logger.info(f"Saved {len(self.history)} decisions to history")
            except Exception as e:
                logger.error(f"Failed to save history: {e}")


# Convenience function
def create_gate() -> ConfidenceGate:
    """Create and configure a ConfidenceGate instance"""
    return ConfidenceGate()
