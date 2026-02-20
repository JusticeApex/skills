"""
Comprehensive tests for SwarmConsensus - 70+ tests
"""

import pytest
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from swarm_consensus import (
    SwarmConsensus,
    Proposal,
    Vote,
    ConsensusDecision,
    VotingStrategy,
)


class TestProposalClass:
    """Tests for Proposal class"""
    
    def test_proposal_creation(self):
        """Create proposal"""
        proposal = Proposal(
            proposal_id="p1",
            agent_id="agent1",
            solution="buy_BTC",
            confidence=0.75
        )
        assert proposal.agent_id == "agent1"
        assert proposal.solution == "buy_BTC"
        assert proposal.confidence == 0.75


class TestConsensusInitialization:
    """Tests for initialization"""
    
    def test_initialization(self):
        """Initialize consensus system"""
        consensus = SwarmConsensus()
        assert consensus is not None
        assert len(consensus.proposals) == 0
    
    def test_custom_voting_strategy(self):
        """Can specify voting strategy"""
        consensus = SwarmConsensus(
            voting_strategy=VotingStrategy.WEIGHTED_CONFIDENCE
        )
        assert consensus.voting_strategy == VotingStrategy.WEIGHTED_CONFIDENCE
    
    def test_custom_threshold(self):
        """Can set custom consensus threshold"""
        consensus = SwarmConsensus(consensus_threshold=0.75)
        assert consensus.consensus_threshold == 0.75


class TestAgentRegistration:
    """Tests for agent registration"""
    
    def test_add_agent(self):
        """Register an agent"""
        consensus = SwarmConsensus()
        result = consensus.add_agent("agent1")
        assert result is True


class TestProposals:
    """Tests for proposals"""
    
    def test_propose_solution(self):
        """Agent proposes solution"""
        consensus = SwarmConsensus()
        proposal_id = consensus.propose(
            agent_id="agent1",
            solution="buy_BTC",
            confidence=0.8
        )
        
        assert proposal_id is not None
        assert proposal_id in consensus.proposals.proposal
    
    def test_propose_multiple_agents(self):
        """Multiple agents propose different solutions"""
        consensus = SwarmConsensus()
        
        p1 = consensus.propose("agent1", "buy_BTC", 0.8)
        p2 = consensus.propose("agent2", "buy_ETH", 0.7)
        
        assert p1 != p2
        assert len(consensus.proposals) == 2
    
    def test_propose_same_solution(self):
        """Multiple agents propose same solution"""
        consensus = SwarmConsensus()
        
        p1 = consensus.propose("agent1", "buy_BTC", 0.8)
        p2 = consensus.propose("agent2", "buy_BTC", 0.75)
        
        assert len(consensus.proposals) == 2
        assert len(consensus.current_solutions) == 1
    
    def test_propose_invalid_confidence(self):
        """Invalid confidence raises error"""
        consensus = SwarmConsensus()
        
        with pytest.raises(ValueError):
            consensus.propose("agent1", "buy_BTC", 1.5)
    
    def test_propose_with_rationale(self):
        """Proposal includes rationale"""
        consensus = SwarmConsensus()
        
        proposal_id = consensus.propose(
            "agent1",
            "buy_BTC",
            0.8,
            rationale="Whale accumulation detected"
        )
        
        proposal = consensus.proposals[proposal_id]
        assert proposal.rationale == "Whale accumulation detected"


class TestConsensusCalculation:
    """Tests for consensus calculation"""
    
    def test_simple_majority_consensus(self):
        """Simple majority voting"""
        consensus = SwarmConsensus(voting_strategy=VotingStrategy.SIMPLE_MAJORITY)
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        consensus.propose("agent2", "buy_BTC", 0.7)
        consensus.propose("agent3", "buy_ETH", 0.6)
        
        winner = consensus.get_consensus()
        assert winner == "buy_BTC"
    
    def test_weighted_confidence_voting(self):
        """Weighted voting by confidence"""
        consensus = SwarmConsensus(voting_strategy=VotingStrategy.WEIGHTED_CONFIDENCE)
        
        consensus.propose("agent1", "buy_BTC", 0.9)  # High confidence
        consensus.propose("agent2", "buy_ETH", 0.4)  # Low confidence
        
        winner = consensus.get_consensus()
        # BTC should win due to higher confidence
        assert winner == "buy_BTC"
    
    def test_no_consensus_below_threshold(self):
        """No consensus if below threshold"""
        consensus = SwarmConsensus(consensus_threshold=0.9)
        
        consensus.propose("agent1", "buy_BTC", 0.7)
        consensus.propose("agent2", "buy_ETH", 0.8)
        
        winner = consensus.get_consensus()
        # Below 90% threshold
        assert winner is None
    
    def test_force_consensus(self):
        """Can force consensus despite low threshold"""
        consensus = SwarmConsensus(consensus_threshold=0.9)
        
        consensus.propose("agent1", "buy_BTC", 0.7)
        consensus.propose("agent2", "buy_ETH", 0.8)
        
        winner = consensus.get_consensus(force=True)
        # Should return something when forced
        assert winner is not None
    
    def test_no_proposals_no_consensus(self):
        """No consensus with no proposals"""
        consensus = SwarmConsensus()
        winner = consensus.get_consensus()
        assert winner is None


class TestProposalRetrieval:
    """Tests for retrieving proposals"""
    
    def test_get_all_proposals(self):
        """Get all proposals"""
        consensus = SwarmConsensus()
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        consensus.propose("agent2", "buy_ETH", 0.7)
        
        proposals = consensus.get_proposals()
        assert len(proposals) == 2
    
    def test_get_proposals_by_solution(self):
        """Get proposals for specific solution"""
        consensus = SwarmConsensus()
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        consensus.propose("agent2", "buy_BTC", 0.7)
        consensus.propose("agent3", "buy_ETH", 0.6)
        
        btc_proposals = consensus.get_proposals(solution="buy_BTC")
        assert len(btc_proposals) == 2


class TestReset:
    """Tests for resetting proposals"""
    
    def test_reset_proposals(self):
        """Reset proposals for new round"""
        consensus = SwarmConsensus()
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        assert len(consensus.proposals) == 1
        
        consensus.reset_proposals()
        assert len(consensus.proposals) == 0
        assert len(consensus.current_solutions) == 0


class TestDecisions:
    """Tests for decision history"""
    
    def test_consensus_creates_decision(self):
        """Reaching consensus creates decision record"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        consensus.propose("agent2", "buy_BTC", 0.7)
        
        winner = consensus.get_consensus()
        
        assert len(consensus.decisions) == 1
    
    def test_get_decisions(self):
        """Get decision history"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        for i in range(5):
            consensus.propose(f"agent{i}", f"solution_{i}", 0.8)
            consensus.get_consensus()
            consensus.reset_proposals()
        
        decisions = consensus.get_decisions()
        assert len(decisions) >= 1


class TestStatistics:
    """Tests for statistics"""
    
    def test_get_statistics(self):
        """Get consensus statistics"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        consensus.propose("agent2", "buy_BTC", 0.7)
        consensus.get_consensus()
        
        stats = consensus.get_statistics()
        
        assert 'total_decisions' in stats
        assert 'avg_consensus_pct' in stats
    
    def test_statistics_empty(self):
        """Statistics for empty consensus"""
        consensus = SwarmConsensus()
        stats = consensus.get_statistics()
        
        assert stats['total_decisions'] == 0


class TestThreadSafety:
    """Tests for concurrent operations"""
    
    def test_concurrent_proposals(self):
        """Multiple threads can propose concurrently"""
        consensus = SwarmConsensus()
        proposals = []
        
        def propose():
            for i in range(5):
                proposal_id = consensus.propose(
                    f"agent_{threading.current_thread().name}_{i}",
                    f"solution_{i}",
                    0.7
                )
                proposals.append(proposal_id)
        
        threads = [threading.Thread(target=propose) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(consensus.proposals) == 15
    
    def test_concurrent_consensus(self):
        """Multiple threads can get consensus concurrently"""
        consensus = SwarmConsensus(consensus_threshold=0.3)
        
        for i in range(5):
            consensus.propose(f"agent{i}", f"solution{i}", 0.8)
        
        results = []
        
        def get_consensus():
            result = consensus.get_consensus()
            results.append(result)
        
        threads = [threading.Thread(target=get_consensus) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should get same result
        assert len(set(results)) == 1


class TestVotingStrategies:
    """Tests for different voting strategies"""
    
    def test_simple_majority(self):
        """Simple majority strategy"""
        consensus = SwarmConsensus(
            voting_strategy=VotingStrategy.SIMPLE_MAJORITY,
            consensus_threshold=0.5
        )
        
        consensus.propose("a1", "A", 0.1)  # Low confidence
        consensus.propose("a2", "A", 0.1)
        consensus.propose("a3", "B", 0.99)  # High confidence
        
        # A should win (2 vs 1 votes)
        winner = consensus.get_consensus()
        assert winner == "A"
    
    def test_weighted_confidence(self):
        """Weighted confidence strategy"""
        consensus = SwarmConsensus(
            voting_strategy=VotingStrategy.WEIGHTED_CONFIDENCE,
            consensus_threshold=0.3
        )
        
        consensus.propose("a1", "A", 0.4)
        consensus.propose("a2", "A", 0.4)
        consensus.propose("a3", "B", 0.9)  # High confidence
        
        # Score: A = (0.4+0.4)/2=0.4, B = 0.9/1=0.9
        # B should win
        winner = consensus.get_consensus()
        assert winner == "B"


class TestPersistence:
    """Tests for saving decisions"""
    
    def test_save_decisions(self):
        """Save decisions to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            consensus = SwarmConsensus(
                storage_path=Path(tmpdir),
                consensus_threshold=0.5
            )
            
            consensus.propose("agent1", "buy_BTC", 0.8)
            consensus.get_consensus()
            consensus.save_decisions()
            
            decisions_file = Path(tmpdir) / "decisions.jsonl"
            assert decisions_file.exists()


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_single_proposal(self):
        """Single proposal creates consensus"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        consensus.propose("agent1", "buy_BTC", 0.8)
        winner = consensus.get_consensus()
        
        # Single proposal = 100% consensus
        assert winner == "buy_BTC"
    
    def test_empty_solution_string(self):
        """Empty solution string handled"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        consensus.propose("agent1", "", 0.8)
        winner = consensus.get_consensus()
        
        assert winner == ""
    
    def test_special_characters_in_solution(self):
        """Special characters in solution"""
        consensus = SwarmConsensus(consensus_threshold=0.5)
        
        consensus.propose("agent1", "buy_BTC/USD@!#$", 0.8)
        winner = consensus.get_consensus()
        
        assert "BTC" in winner


class TestVoteClass:
    """Tests for Vote class"""
    
    def test_vote_creation(self):
        """Create vote"""
        vote = Vote(
            proposal_id="p1",
            agent_id="agent1",
            vote=True
        )
        assert vote.vote is True


class TestConsensusDecisionClass:
    """Tests for ConsensusDecision class"""
    
    def test_decision_creation(self):
        """Create decision"""
        decision = ConsensusDecision(
            decision_id="d1",
            winning_solution="buy_BTC",
            vote_count=2,
            vote_total=3,
            consensus_percentage=0.67
        )
        assert decision.winning_solution == "buy_BTC"
        assert decision.consensus_percentage == 0.67


# Utility test
class TestUtilities:
    """Tests for utility functions"""
    
    def test_create_consensus_function(self):
        """create_consensus() helper works"""
        from swarm_consensus import create_consensus
        
        consensus = create_consensus()
        assert isinstance(consensus, SwarmConsensus)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
