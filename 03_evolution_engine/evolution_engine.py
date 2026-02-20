"""
EVOLUTION ENGINE - Autonomous Self-Improvement System
=====================================================

Learns from outcomes, identifies winning strategies, and automatically applies
improvements. Enables systems to evolve without human intervention.

Features:
- Pattern detection from telemetry
- Winning strategy identification (>90% success)
- Automatic strategy application
- Genealogy tracking
- Continuous improvement cycles
- Real-time learning

Author: Justice Apex LLC
License: MIT
"""

import threading
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from collections import deque
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """A strategy/approach with performance metrics"""
    id: str
    name: str
    success_count: int = 0
    failure_count: int = 0
    total_reward: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    generation: int = 1
    parent_id: Optional[str] = None
    
    @property
    def total_attempts(self) -> int:
        """Total attempts (success + failure)"""
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """Success rate (0.0-1.0)"""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts
    
    @property
    def average_reward(self) -> float:
        """Average reward per attempt"""
        if self.total_attempts == 0:
            return 0.0
        return self.total_reward / self.total_attempts
    
    @property
    def is_winning(self) -> bool:
        """Is this a winning strategy (>90% success, >10 attempts)"""
        return self.success_rate >= 0.9 and self.total_attempts >= 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Outcome:
    """Outcome from applying a strategy"""
    strategy_id: str
    success: bool
    reward: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class EvolutionEngine:
    """
    Autonomous self-improvement engine.
    
    Learns from outcomes, identifies winning patterns, and automatically
    improves without human intervention.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        success_threshold: float = 0.9,
        min_attempts: int = 10
    ):
        """
        Initialize evolution engine
        
        Args:
            storage_path: Path for storing strategies and genealogy
            success_threshold: Threshold for "winning" strategies (0.0-1.0)
            min_attempts: Minimum attempts before marking as winning
        """
        self.storage_path = storage_path or Path("evolution_engine_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.success_threshold = success_threshold
        self.min_attempts = min_attempts
        
        # Strategies registry
        self.strategies: Dict[str, Strategy] = {}
        
        # Outcomes history
        self.outcomes: deque = deque(maxlen=10000)
        
        # Genealogy tracking
        self.genealogy: Dict[str, List[str]] = {}  # parent_id -> [child_ids]
        
        # Current generation number
        self.current_generation = 1
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Load strategies if they exist
        self._load_strategies()
        
        logger.info(f"EvolutionEngine initialized with {len(self.strategies)} strategies")
    
    def create_strategy(
        self,
        name: str,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Create a new strategy
        
        Args:
            name: Strategy name
            parent_id: Parent strategy ID (for genealogy)
        
        Returns:
            Strategy ID
        """
        with self._lock:
            strategy_id = self._generate_id()
            generation = 1
            
            if parent_id and parent_id in self.strategies:
                parent = self.strategies[parent_id]
                generation = parent.generation + 1
                
                # Track genealogy
                if parent_id not in self.genealogy:
                    self.genealogy[parent_id] = []
                self.genealogy[parent_id].append(strategy_id)
            
            strategy = Strategy(
                id=strategy_id,
                name=name,
                parent_id=parent_id,
                generation=generation
            )
            
            self.strategies[strategy_id] = strategy
            
            logger.info(f"Created strategy '{name}' (ID: {strategy_id})")
            return strategy_id
    
    def record_outcome(
        self,
        strategy_id: str,
        success: bool,
        reward: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Record outcome from a strategy
        
        Args:
            strategy_id: Strategy that was applied
            success: Whether it succeeded
            reward: Reward value (for optimization)
            context: Additional context about the attempt
            error: Error message if failed
        """
        with self._lock:
            if strategy_id not in self.strategies:
                raise ValueError(f"Unknown strategy: {strategy_id}")
            
            # Update strategy metrics
            strategy = self.strategies[strategy_id]
            if success:
                strategy.success_count += 1
            else:
                strategy.failure_count += 1
            
            strategy.total_reward += reward
            strategy.last_used = datetime.now().isoformat()
            
            # Record outcome
            outcome = Outcome(
                strategy_id=strategy_id,
                success=success,
                reward=reward,
                context=context or {},
                error=error
            )
            self.outcomes.appendleft(outcome)
            
            # Log
            log_fn = logger.info if success else logger.warning
            log_fn(f"Strategy '{strategy.name}': {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    def get_best_strategy(self, generation: Optional[int] = None) -> Optional[str]:
        """
        Get best performing strategy
        
        Args:
            generation: Filter to specific generation (None = all)
        
        Returns:
            Strategy ID of best performer, or None
        """
        with self._lock:
            candidates = []
            
            for strategy in self.strategies.values():
                if generation is not None and strategy.generation != generation:
                    continue
                
                candidates.append(strategy)
            
            if not candidates:
                return None
            
            # Sort by success rate, then by average reward
            best = max(
                candidates,
                key=lambda s: (s.success_rate, s.average_reward)
            )
            
            return best.id if best else None
    
    def get_winning_strategies(self) -> List[str]:
        """
        Get all winning strategies (>success_threshold)
        
        Returns:
            List of winning strategy IDs
        """
        with self._lock:
            winning = [
                s.id for s in self.strategies.values()
                if (s.success_rate >= self.success_threshold and
                    s.total_attempts >= self.min_attempts)
            ]
            
            return sorted(
                winning,
                key=lambda sid: self.strategies[sid].success_rate,
                reverse=True
            )
    
    def apply_strategy(self, strategy_id: str) -> bool:
        """
        Apply a strategy (mark as applied)
        
        Args:
            strategy_id: Strategy to apply
        
        Returns:
            True if applied successfully
        """
        with self._lock:
            if strategy_id not in self.strategies:
                return False
            
            strategy = self.strategies[strategy_id]
            strategy.last_used = datetime.now().isoformat()
            
            logger.info(f"Applied strategy: {strategy.name}")
            return True
    
    def create_variant(self, parent_id: str, name: str) -> str:
        """
        Create variant of a winning strategy
        
        Args:
            parent_id: Parent strategy ID
            name: Name for variant
        
        Returns:
            New strategy ID
        """
        if parent_id not in self.strategies:
            raise ValueError(f"Unknown parent: {parent_id}")
        
        return self.create_strategy(name, parent_id=parent_id)
    
    def evolve(self) -> Optional[str]:
        """
        Evolution cycle: find winning strategies and create variants
        
        Returns:
            ID of newly created variant, or None if no improvement possible
        """
        with self._lock:
            winning = self.get_winning_strategies()
            
            if not winning:
                logger.info("No winning strategies to evolve")
                return None
            
            # Pick best winner
            best_winner = max(
                winning,
                key=lambda sid: self.strategies[sid].success_rate
            )
            
            parent = self.strategies[best_winner]
            
            # Create variant
            variant_name = f"{parent.name}_v{parent.generation + 1}"
            variant_id = self.create_strategy(variant_name, parent_id=best_winner)
            
            logger.info(f"Evolved: {parent.name} → {variant_name}")
            return variant_id
    
    def get_genealogy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get genealogical info for a strategy
        
        Args:
            strategy_id: Strategy ID
        
        Returns:
            Genealogy info (parents, children, generation)
        """
        with self._lock:
            if strategy_id not in self.strategies:
                return {}
            
            strategy = self.strategies[strategy_id]
            
            return {
                'id': strategy_id,
                'name': strategy.name,
                'generation': strategy.generation,
                'parent_id': strategy.parent_id,
                'children': self.genealogy.get(strategy_id, []),
                'success_rate': strategy.success_rate
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get engine statistics
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            if not self.strategies:
                return {'total_strategies': 0}
            
            strategies = list(self.strategies.values())
            
            outcomes_success = sum(1 for o in self.outcomes if o.success)
            outcomes_total = len(self.outcomes)
            overall_success_rate = outcomes_success / outcomes_total if outcomes_total > 0 else 0
            
            return {
                'total_strategies': len(self.strategies),
                'current_generation': max(s.generation for s in strategies),
                'winning_strategies': len(self.get_winning_strategies()),
                'total_outcomes_recorded': outcomes_total,
                'overall_success_rate': overall_success_rate,
                'avg_attempts_per_strategy': sum(s.total_attempts for s in strategies) / len(strategies),
                'best_strategy': self.get_best_strategy()
            }
    
    def get_outcomes(
        self,
        strategy_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Outcome]:
        """
        Get outcomes history
        
        Args:
            strategy_id: Filter by strategy (None = all)
            limit: Maximum to return
        
        Returns:
            List of outcomes
        """
        with self._lock:
            outcomes = list(self.outcomes)
            
            if strategy_id:
                outcomes = [o for o in outcomes if o.strategy_id == strategy_id]
            
            return outcomes[:limit]
    
    def save_strategies(self):
        """Save strategies to disk"""
        strategies_file = self.storage_path / "strategies.jsonl"
        genealogy_file = self.storage_path / "genealogy.json"
        
        with self._lock:
            try:
                # Save strategies
                with open(strategies_file, 'w') as f:
                    for strategy in self.strategies.values():
                        f.write(json.dumps(strategy.to_dict()) + '\n')
                
                # Save genealogy
                with open(genealogy_file, 'w') as f:
                    json.dump(self.genealogy, f, indent=2)
                
                logger.info(f"Saved {len(self.strategies)} strategies")
            
            except Exception as e:
                logger.error(f"Failed to save strategies: {e}")
    
    # Private methods
    
    def _generate_id(self) -> str:
        """Generate unique strategy ID"""
        timestamp = datetime.now().isoformat()
        data = f"{timestamp}_{len(self.strategies)}".encode()
        return hashlib.md5(data).hexdigest()[:12]
    
    def _load_strategies(self):
        """Load strategies from disk"""
        strategies_file = self.storage_path / "strategies.jsonl"
        
        if strategies_file.exists():
            try:
                count = 0
                for line in strategies_file.read_text().split('\n'):
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    strategy = Strategy(
                        id=data['id'],
                        name=data['name'],
                        success_count=data['success_count'],
                        failure_count=data['failure_count'],
                        total_reward=data['total_reward'],
                        created_at=data['created_at'],
                        last_used=data['last_used'],
                        generation=data['generation'],
                        parent_id=data['parent_id']
                    )
                    self.strategies[strategy.id] = strategy
                    count += 1
                
                logger.info(f"Loaded {count} strategies")
            
            except Exception as e:
                logger.error(f"Failed to load strategies: {e}")


def create_engine() -> EvolutionEngine:
    """Create and return an EvolutionEngine instance"""
    return EvolutionEngine()
