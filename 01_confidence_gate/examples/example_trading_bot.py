"""
EXAMPLE: Autonomous Trading Bot with ConfidenceGate Quality Control
====================================================================

This example demonstrates how to build a safe, autonomous trading bot that:
- Auto-executes small trades (HIGH confidence)
- Logs medium trades but executes (MEDIUM confidence)
- Pauses large trades for human review (LOW confidence)
- Requires explicit approval for extreme positions (CRITICAL confidence)

The bot monitors market volatility, error rates, and losing streaks to dynamically
adjust confidence levels.
"""

import random
from datetime import datetime
from confidence_gate import ConfidenceGate, ActionConfidence, RiskFactor


class TradingBot:
    """Autonomous trading bot with confidence gates"""
    
    def __init__(self):
        self.gate = ConfidenceGate()
        self.balance = 10000  # $10,000 starting capital
        self.trades_executed = 0
        self.trades_paused = 0
        self.errors = 0
        self.losing_streak = 0
        
        # Register trading actions
        self._register_actions()
    
    def _register_actions(self):
        """Register trading actions with confidence levels"""
        
        # Small trades auto-execute
        self.gate.register_action(
            'buy_small',
            ActionConfidence.HIGH,
            custom_threshold=0.7,
            risk_adjustments={
                RiskFactor.VOLATILITY: -0.1,
                RiskFactor.ERROR_RATE: -0.05
            }
        )
        
        # Medium trades logged and executed
        self.gate.register_action(
            'buy_medium',
            ActionConfidence.MEDIUM,
            custom_threshold=0.5,
            risk_adjustments={
                RiskFactor.VOLATILITY: -0.2,
                RiskFactor.ERROR_RATE: -0.15,
                RiskFactor.LOSING_STREAK: -0.1
            }
        )
        
        # Large trades require review
        self.gate.register_action(
            'buy_large',
            ActionConfidence.LOW,
            custom_threshold=0.3,
            risk_adjustments={
                RiskFactor.VOLATILITY: -0.3,
                RiskFactor.ERROR_RATE: -0.2,
                RiskFactor.LOSING_STREAK: -0.25,
                RiskFactor.LARGE_AMOUNT: -0.15
            }
        )
        
        # Extreme positions always require approval
        self.gate.register_action(
            'buy_extreme',
            ActionConfidence.CRITICAL,
            risk_adjustments={
                RiskFactor.LARGE_AMOUNT: -0.5
            }
        )
    
    def get_current_market_conditions(self) -> dict:
        """Get current market volatility, error rate, etc."""
        volatility = random.uniform(0.2, 1.0)  # 20-100% volatility
        error_rate = (self.errors / max(self.trades_executed, 1)) * 0.5
        
        return {
            'volatility': min(1.0, volatility),
            'error_rate': min(1.0, error_rate),
            'losing_streak': self.losing_streak,
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_trade(self, action: str, amount: float) -> dict:
        """
        Evaluate whether a trade should execute
        
        Args:
            action: 'buy_small', 'buy_medium', 'buy_large', or 'buy_extreme'
            amount: Dollar amount to trade
        
        Returns:
            Dictionary with decision details
        """
        market_conditions = self.get_current_market_conditions()
        
        # Evaluate the trade
        result = self.gate.evaluate_action(
            action=action,
            context={
                'amount': amount,
                'timestamp': market_conditions['timestamp'],
                'balance': self.balance
            },
            risk_factors={
                'volatility': market_conditions['volatility'],
                'error_rate': market_conditions['error_rate'],
                'losing_streak': market_conditions['losing_streak'],
                'large_amount': 1.0 if amount > 2000 else 0.0
            }
        )
        
        return {
            'action': action,
            'amount': amount,
            'should_execute': result.should_execute,
            'confidence': result.confidence_value,
            'explanation': result.explanation,
            'market_conditions': market_conditions
        }
    
    def execute_trade(self, action: str, amount: float) -> bool:
        """
        Execute a trade after confidence gate evaluation
        
        Returns:
            True if successful, False if failed
        """
        decision = self.evaluate_trade(action, amount)
        
        print(f"\n{'='*60}")
        print(f"Trade Evaluation: {decision['action']} - ${decision['amount']:.2f}")
        print(f"{'='*60}")
        print(f"Confidence: {decision['confidence']:.2%}")
        print(f"Decision: {'✅ EXECUTE' if decision['should_execute'] else '⏸️ PAUSED'}")
        print(f"Explanation: {decision['explanation']}")
        print(f"Market Conditions: {decision['market_conditions']}")
        
        if not decision['should_execute']:
            self.trades_paused += 1
            print("⏸️ Paused for human review!")
            return False
        
        # Execute the trade
        try:
            # Simulate trade execution
            if random.random() > 0.9:  # 10% failure rate for simulation
                raise Exception("Trade execution failed!")
            
            self.balance -= amount
            self.trades_executed += 1
            self.losing_streak = 0  # Reset on success
            
            print(f"✅ Trade executed! New balance: ${self.balance:.2f}")
            return True
        
        except Exception as e:
            self.errors += 1
            self.losing_streak += 1
            print(f"❌ Trade failed: {e}")
            return False
    
    def run_trading_session(self, num_trades: int = 10):
        """Run a trading session with multiple trades"""
        print(f"\n{'='*60}")
        print(f"STARTING TRADING SESSION: {num_trades} trades")
        print(f"{'='*60}")
        
        for i in range(num_trades):
            # Randomly choose trade size
            trade_type = random.choice(['small', 'medium', 'large', 'extreme'])
            amounts = {
                'small': random.uniform(50, 200),
                'medium': random.uniform(200, 1000),
                'large': random.uniform(1000, 3000),
                'extreme': random.uniform(3000, 8000)
            }
            
            amount = amounts[trade_type]
            
            # Skip if insufficient balance
            if amount > self.balance:
                print(f"\n⚠️ Insufficient balance for ${amount:.2f} trade")
                continue
            
            # Execute trade
            self.execute_trade(f'buy_{trade_type}', amount)
        
        # Print session summary
        self._print_session_summary()
    
    def _print_session_summary(self):
        """Print trading session summary"""
        print(f"\n{'='*60}")
        print(f"SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"Trades Executed: {self.trades_executed}")
        print(f"Trades Paused: {self.trades_paused}")
        print(f"Errors: {self.errors}")
        print(f"Final Balance: ${self.balance:.2f}")
        print(f"Success Rate: {(self.trades_executed / max(self.trades_executed + self.errors, 1)) * 100:.1f}%")
        
        # Print confidence gate statistics
        stats = self.gate.get_statistics()
        print(f"\nConfidence Gate Statistics:")
        print(f"  Total Decisions: {stats['total_decisions']}")
        print(f"  Execution Rate: {stats['execution_rate']:.1%}")
        print(f"  Avg Confidence: {stats['avg_confidence']:.2f}")


if __name__ == '__main__':
    # Create bot
    bot = TradingBot()
    
    # Run trading session
    bot.run_trading_session(num_trades=15)
    
    # Show decision history
    print(f"\n{'='*60}")
    print("DECISION HISTORY (Last 10)")
    print(f"{'='*60}")
    
    for decision in bot.gate.get_history(limit=10):
        status = '✅' if decision.should_execute else '⏸️'
        print(f"{status} {decision.action:20s} "
              f"confidence={decision.confidence_value:.2f} "
              f"({decision.timestamp})")
