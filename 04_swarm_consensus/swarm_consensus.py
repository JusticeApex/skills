"""
SWARM CONSENSUS - Democratic Multi-Agent Decision System
=========================================================

Enables multiple AI agents to collectively decide through democratic voting.
Each agent proposes solutions with confidence scores, majority wins.

Features:
- Multi-agent proposals
- Weighted voting by confidence
- Consensus threshold configuration
- Complete decision audit trail
- Automatic conflict resolution
- Real-time voting

Author: Justice Apex LLC
License: MIT
"""

import threading
import time
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Proposal:
    """A proposal from an agent"""
    proposal_id: str
    agent_id: str
    solution: str
    confidence: float  # 0.0-1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    rationale: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Vote:
    """A vote on a proposal"""
    proposal_id: str
    agent_id: str
    vote: bool  # True = for, False = against
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ConsensusDecision:
    """Final consensus decision"""
    decision_id: str
    winning_solution: str
    vote_count: int
    vote_total: int
    consensus_percentage: float
    proposals: List[Proposal] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'decision_id': self.decision_id,
            'winning_solution': self.winning_solution,
            'vote_count': self.vote_count,
            'vote_total': self.vote_total,
            'consensus_percentage': self.consensus_percentage,
            'timestamp': self.timestamp
        }


class VotingStrategy(Enum):
    """Voting strategies"""
    SIMPLE_MAJORITY = "simple_majority"  # >50%
    WEIGHTED_CONFIDENCE = "weighted_confidence"  # Weight by confidence
    SUPERMAJORITY = "supermajority"  # >66%
    UNANIMOUS = "unanimous"  # 100%


class SwarmConsensus:
    """
    Democratic multi-agent decision system.
    
    Multiple agents propose solutions with confidence scores.
    Voting system determines consensus via majority rule or weighted voting.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        voting_strategy: VotingStrategy = VotingStrategy.SIMPLE_MAJORITY,
        consensus_threshold: float = 0.5
    ):
        """
        Initialize consensus system
        
        Args:
            storage_path: Path for storing decisions
            voting_strategy: How to count votes
            consensus_threshold: Minimum percentage for consensus (0.0-1.0)
        """
        self.storage_path = storage_path or Path("swarm_consensus_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.voting_strategy = voting_strategy
        self.consensus_threshold = consensus_threshold
        
        # Proposals by ID
        self.proposals: Dict[str, Proposal] = {}
        
        # Votes
        self.votes: Dict[str, List[Vote]] = defaultdict(list)
        
        # Consensus decisions history
        self.decisions: Dict[str, ConsensusDecision] = {}
        
        # Solutions being voted on
        self.current_solutions: Set[str] = set()
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info(f"SwarmConsensus initialized with {voting_strategy.value} voting")
    
    def add_agent(self, agent_id: str) -> bool:
        """
        Register an agent
        
        Args:
            agent_id: Unique agent identifier
        
        Returns:
            True if registered successfully
        """
        # Agents are registered implicitly when they propose
        logger.info(f"Agent registered: {agent_id}")
        return True
    
    def propose(
        self,
        agent_id: str,
        solution: str,
        confidence: float = 0.5,
        rationale: Optional[str] = None
    ) -> str:
        """
        Agent proposes a solution
        
        Args:
            agent_id: Agent making proposal
            solution: The proposed solution
            confidence: Agent's confidence (0.0-1.0)
            rationale: Optional explanation
        
        Returns:
            Proposal ID
        """
        with self._lock:
            if not (0.0 <= confidence <= 1.0):
                raise ValueError("Confidence must be 0.0-1.0")
            
            proposal_id = self._generate_id()
            
            proposal = Proposal(
                proposal_id=proposal_id,
                agent_id=agent_id,
                solution=solution,
                confidence=confidence,
                rationale=rationale
            )
            
            self.proposals[proposal_id] = proposal
            self.current_solutions.add(solution)
            
            logger.info(f"Proposal from {agent_id}: {solution} (confidence: {confidence:.2f})")
            return proposal_id
    
    def get_proposals(self, solution: Optional[str] = None) -> List[Proposal]:
        """
        Get all proposals
        
        Args:
            solution: Filter by solution (None = all)
        
        Returns:
            List of proposals
        """
        with self._lock:
            proposals = list(self.proposals.values())
            
            if solution:
                proposals = [p for p in proposals if p.solution == solution]
            
            return proposals
    
    def get_consensus(self, force: bool = False) -> Optional[str]:
        """
        Calculate consensus from current proposals
        
        Args:
            force: Force decision even if below threshold
        
        Returns:
            Winning solution, or None if no consensus
        """
        with self._lock:
            if not self.current_solutions:
                return None
            
            # Count votes/confidence by solution
            solution_scores = {}
            solution_votes = {}
            
            for solution in self.current_solutions:
                proposals_for_solution = [
                    p for p in self.proposals.values()
                    if p.solution == solution
                ]
                
                if self.voting_strategy == VotingStrategy.WEIGHTED_CONFIDENCE:
                    # Weight by confidence
                    score = sum(p.confidence for p in proposals_for_solution)
                    max_score = len(proposals_for_solution)
                    solution_scores[solution] = score / max_score if max_score > 0 else 0
                else:
                    # Simple majority
                    solution_scores[solution] = len(proposals_for_solution)
                
                solution_votes[solution] = len(proposals_for_solution)
            
            if not solution_scores:
                return None
            
            # Find winner
            winner = max(solution_scores.keys(), key=lambda s: solution_scores[s])
            winner_votes = solution_votes[winner]
            total_proposals = len(self.proposals)
            consensus_pct = winner_votes / total_proposals if total_proposals > 0 else 0
            
            # Check threshold
            if consensus_pct < self.consensus_threshold and not force:
                logger.warning(f"No consensus (winning {consensus_pct:.1%})")
                return None
            
            # Record decision
            decision_id = self._generate_id()
            decision = ConsensusDecision(
                decision_id=decision_id,
                winning_solution=winner,
                vote_count=winner_votes,
                vote_total=total_proposals,
                consensus_percentage=consensus_pct,
                proposals=[p for p in self.proposals.values()]
            )
            
            self.decisions[decision_id] = decision
            
            logger.info(f"Consensus: {winner} ({consensus_pct:.1%} agreement)")
            return winner
    
    def reset_proposals(self) -> None:
        """Clear current proposals for next round"""
        with self._lock:
            self.proposals.clear()
            self.current_solutions.clear()
            self.votes.clear()
            
            logger.info("Proposals reset for next round")
    
    def get_decisions(self, limit: int = 100) -> List[ConsensusDecision]:
        """
        Get decision history
        
        Args:
            limit: Maximum decisions to return
        
        Returns:
            List of decisions
        """
        with self._lock:
            decisions = list(self.decisions.values())
            decisions.sort(key=lambda d: d.timestamp, reverse=True)
            return decisions[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get consensus statistics
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            if not self.decisions:
                return {'total_decisions': 0}
            
            decisions = list(self.decisions.values())
            
            return {
                'total_decisions': len(decisions),
                'avg_consensus_pct': sum(d.consensus_percentage for d in decisions) / len(decisions),
                'min_consensus_pct': min(d.consensus_percentage for d in decisions),
                'max_consensus_pct': max(d.consensus_percentage for d in decisions),
                'current_proposals': len(self.proposals)
            }
    
    def save_decisions(self):
        """Save decisions to disk"""
        decisions_file = self.storage_path / "decisions.jsonl"
        
        with self._lock:
            try:
                with open(decisions_file, 'w') as f:
                    for decision in self.decisions.values():
                        f.write(json.dumps(decision.to_dict()) + '\n')
                
                logger.info(f"Saved {len(self.decisions)} decisions")
            
            except Exception as e:
                logger.error(f"Failed to save decisions: {e}")
    
    # Private methods
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        timestamp = datetime.now().isoformat()
        data = f"{timestamp}_{len(self.proposals)}".encode()
        return hashlib.md5(data).hexdigest()[:12]


def create_consensus() -> SwarmConsensus:
    """Create and return SwarmConsensus instance"""
    return SwarmConsensus()
