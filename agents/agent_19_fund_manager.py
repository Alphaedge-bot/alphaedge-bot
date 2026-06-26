"""
AlphaEdge Agent 19 – Fund Manager
Decision resolver, final trade decision, position size, stop loss, targets
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class FundManager:
    """Fund Manager – Final decision authority for trades and allocations"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "fund_manager"
        self.running = False
        
        # Portfolio state
        self.portfolio = {}
        self.allocations = {}
        self.trade_history = []
        self.total_capital = 0
        
        # Position limits
        self.max_positions = 18
        self.max_position_size = 0.06  # 6%
        self.min_position_size = 0.01   # 1%
        
    async def start(self):
        """Start the fund manager"""
        logger.info("Fund Manager starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("trade_decision_request", self.handle_trade_decision)
        await self.event_bus.subscribe("position_close_request", self.handle_position_close)
        await self.event_bus.subscribe("portfolio_rebalance_request", self.handle_portfolio_rebalance)
        
        # Start management cycle
        asyncio.create_task(self.run_management_cycle())
        
        logger.info("Fund Manager running")
        
    async def stop(self):
        """Stop the fund manager"""
        self.running = False
        logger.info("Fund Manager stopped")
        
    async def run_management_cycle(self):
        """Run regular management cycle"""
        while self.running:
            try:
                # Update capital
                await self.update_capital()
                
                # Check position limits
                await self.check_position_limits()
                
                # Publish portfolio update
                await self.publish_portfolio_update()
                
            except Exception as e:
                logger.error(f"Management cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_trade_decision(self, event: Event):
        """Handle trade decision requests"""
        if not self.running:
            return
            
        proposal = event.data.get('proposal')
        proposal_id = proposal.get('id')
        token = proposal.get('token')
        
        logger.info(f"Trade decision requested for {token}")
        
        # Calculate position size
        position_size = await self.calculate_position_size(token, proposal)
        
        # Calculate stop loss
        stop_loss = await self.calculate_stop_loss(token, proposal, position_size)
        
        # Calculate targets
        targets = await self.calculate_targets(token, proposal)
        
        # Make final decision
        decision = await self.make_decision(proposal, position_size, stop_loss, targets)
        
        # Publish decision
        response = Event(
            event_type="trade_decision_response",
            data={
                'proposal_id': proposal_id,
                'token': token,
                'decision': decision,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'targets': targets,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
        logger.info(f"Decision for {token}: {decision}")
        
    async def calculate_position_size(self, token: str, proposal: Dict) -> float:
        """Calculate optimal position size"""
        tps = proposal.get('tps', 0)
        risk_score = proposal.get('risk_score', 0)
        
        # Base size
        if tps >= 90:
            base_size = 0.06  # 6%
        elif tps >= 85:
            base_size = 0.05  # 5%
        elif tps >= 82:
            base_size = 0.04  # 4%
        else:
            base_size = 0.02  # 2%
            
        # Adjust for risk
        risk_adjustment = 1 - (risk_score / 100)
        size = base_size * risk_adjustment
        
        # Cap at limits
        size = max(self.min_position_size, min(self.max_position_size, size))
        
        # Adjust for portfolio concentration
        current_positions = len(self.portfolio)
        if current_positions >= self.max_positions:
            size = size * 0.5  # Reduce size if many positions
            
        return size
        
    async def calculate_stop_loss(self, token: str, proposal: Dict, 
                                  position_size: float) -> float:
        """Calculate stop loss level"""
        entry_price = proposal.get('entry_price', 0)
        
        # Get volatility-based stop
        atr = proposal.get('atr', 0)
        if atr > 0:
            stop_distance = atr * 1.5
        else:
            stop_distance = entry_price * 0.08  # 8% default
            
        stop_loss = entry_price - stop_distance
        
        # Ensure stop loss is reasonable
        min_stop = entry_price * 0.92  # Max 8% loss
        if stop_loss < min_stop:
            stop_loss = min_stop
            
        return stop_loss
        
    async def calculate_targets(self, token: str, proposal: Dict) -> List[float]:
        """Calculate profit targets"""
        entry_price = proposal.get('entry_price', 0)
        tps = proposal.get('tps', 0)
        
        # Determine target multipliers based on TPS
        if tps >= 90:
            multipliers = [1.15, 1.30, 1.50]  # 15%, 30%, 50%
        elif tps >= 85:
            multipliers = [1.12, 1.25, 1.40]  # 12%, 25%, 40%
        else:
            multipliers = [1.10, 1.20, 1.30]  # 10%, 20%, 30%
            
        targets = [entry_price * m for m in multipliers]
        return targets
        
    async def make_decision(self, proposal: Dict, position_size: float,
                           stop_loss: float, targets: List[float]) -> str:
        """Make final trade decision"""
        # Check if position limit reached
        if len(self.portfolio) >= self.max_positions:
            return 'reject_position_limit'
            
        # Check capital availability
        capital = await self.state_manager.get('available_capital', 0)
        required = position_size * capital
        
        if required > capital:
            return 'reject_insufficient_capital'
            
        # Check if token already held
        if proposal.get('token') in self.portfolio:
            return 'reject_already_held'
            
        # Check risk score
        risk_score = proposal.get('risk_score', 0)
        if risk_score > 70:
            return 'reject_high_risk'
            
        # Check macro conditions
        macro_score = await self.state_manager.get('macro_score', 50)
        if macro_score < 40:
            return 'reject_poor_macro'
            
        return 'approve'
        
    async def handle_position_close(self, event: Event):
        """Handle position close requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        reason = event.data.get('reason')
        
        if token in self.portfolio:
            # Remove position
            self.portfolio.pop(token)
            logger.info(f"Closed position: {token} ({reason})")
            
            # Publish position closed
            response = Event(
                event_type="position_closed",
                data={
                    'token': token,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(response)
            
    async def handle_portfolio_rebalance(self, event: Event):
        """Handle portfolio rebalancing"""
        if not self.running:
            return
            
        logger.info("Portfolio rebalancing triggered")
        
        # Calculate target allocations
        target_allocs = await self.calculate_target_allocations()
        
        # Execute rebalance
        rebalance_data = {
            'target_allocations': target_allocs,
            'current_positions': len(self.portfolio),
            'actions': self.generate_rebalance_actions(target_allocs),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="rebalance_executed",
            data=rebalance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(response)
        
        logger.info(f"Rebalanced portfolio: {len(target_allocs)} targets")
        
    async def calculate_target_allocations(self) -> Dict[str, float]:
        """Calculate target allocations for rebalancing"""
        # Get current regime
        regime = await self.state_manager.get('current_regime', 'neutral')
        
        # Define allocation by regime
        allocations = {
            'bull': {'micro': 0.12, 'small': 0.30, 'mid': 0.40},
            'alt': {'micro': 0.10, 'small': 0.35, 'mid': 0.35},
            'accumulation': {'micro': 0.08, 'small': 0.25, 'mid': 0.30},
            'neutral': {'micro': 0.06, 'small': 0.20, 'mid': 0.25},
            'bear': {'micro': 0.04, 'small': 0.10, 'mid': 0.15},
            'crash': {'micro': 0.02, 'small': 0.05, 'mid': 0.08}
        }
        
        return allocations.get(regime, allocations['neutral'])
        
    def generate_rebalance_actions(self, target_allocs: Dict) -> List[Dict]:
        """Generate rebalance actions"""
        actions = []
        current_positions = len(self.portfolio)
        
        # Calculate actions based on current vs target
        for category, target in target_allocs.items():
            current = self.get_current_allocation(category)
            diff = target - current
            
            if abs(diff) > 0.02:  # 2% threshold
                actions.append({
                    'category': category,
                    'action': 'increase' if diff > 0 else 'decrease',
                    'amount': abs(diff),
                    'target': target,
                    'current': current
                })
                
        return actions
        
    def get_current_allocation(self, category: str) -> float:
        """Get current allocation for a category"""
        # Simplified: count positions in category
        if not self.portfolio:
            return 0
            
        count = len(self.portfolio)
        category_count = sum(1 for p in self.portfolio.values() 
                           if p.get('category') == category)
        
        return category_count / count if count > 0 else 0
        
    async def update_capital(self):
        """Update total capital"""
        # Get from state
        total = await self.state_manager.get('total_capital', 0)
        if total > 0:
            self.total_capital = total
            
    async def check_position_limits(self):
        """Check position limits"""
        if len(self.portfolio) >= self.max_positions:
            # Pause new entries
            await self.state_manager.set('pause_entries', True)
        else:
            await self.state_manager.set('pause_entries', False)
            
    async def publish_portfolio_update(self):
        """Publish portfolio data update"""
        portfolio_data = {
            'total_capital': self.total_capital,
            'positions': len(self.portfolio),
            'max_positions': self.max_positions,
            'allocations': self.allocations,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="portfolio_update",
            data=portfolio_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get fund manager status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_capital': self.total_capital,
            'positions': len(self.portfolio),
            'max_positions': self.max_positions,
            'trade_history': len(self.trade_history),
            'timestamp': datetime.now().isoformat()
        }
