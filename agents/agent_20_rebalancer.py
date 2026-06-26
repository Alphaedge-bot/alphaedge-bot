"""
AlphaEdge Agent 20 – Portfolio Rebalancer
Multi-asset exposure, profit taking, collateral ratios, daily rebalance
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """Portfolio Rebalancer – Manages multi-asset exposure and daily rebalancing"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "rebalancer"
        self.running = False
        
        # Portfolio state
        self.portfolio = {}
        self.target_allocations = {}
        self.current_allocations = {}
        self.rebalance_history = []
        
        # Rebalance thresholds
        self.rebalance_threshold = 0.05  # 5% drift triggers rebalance
        self.profit_take_threshold = 0.20  # 20% profit triggers partial take
        
        # Asset classes
        self.asset_classes = {
            'micro': {'weight': 0.12, 'max_positions': 6},
            'small': {'weight': 0.30, 'max_positions': 10},
            'mid': {'weight': 0.40, 'max_positions': 12},
            'stable': {'weight': 0.18, 'max_positions': 3}
        }
        
    async def start(self):
        """Start the rebalancer"""
        logger.info("Portfolio Rebalancer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("rebalance_request", self.handle_rebalance_request)
        await self.event_bus.subscribe("position_update", self.handle_position_update)
        await self.event_bus.subscribe("profit_take_request", self.handle_profit_take)
        
        # Start daily rebalance cycle
        asyncio.create_task(self.run_rebalance_cycle())
        
        logger.info("Portfolio Rebalancer running")
        
    async def stop(self):
        """Stop the rebalancer"""
        self.running = False
        logger.info("Portfolio Rebalancer stopped")
        
    async def run_rebalance_cycle(self):
        """Run daily rebalance cycle"""
        last_rebalance = datetime.now()
        
        while self.running:
            try:
                # Update current allocations
                await self.update_allocations()
                
                # Check if rebalance needed
                if await self.should_rebalance():
                    await self.execute_rebalance()
                    
                # Check profit taking
                await self.check_profit_taking()
                
                # Publish rebalance update
                await self.publish_rebalance_update()
                
            except Exception as e:
                logger.error(f"Rebalance cycle error: {e}")
                
            # Wait until next cycle (daily)
            await asyncio.sleep(3600)  # 1 hour check
            
    async def handle_rebalance_request(self, event: Event):
        """Handle rebalance requests"""
        if not self.running:
            return
            
        trigger = event.data.get('trigger', 'manual')
        logger.info(f"Rebalance triggered: {trigger}")
        
        await self.execute_rebalance()
        
    async def handle_position_update(self, event: Event):
        """Handle position updates"""
        if not self.running:
            return
            
        position = event.data
        token = position.get('token')
        
        self.portfolio[token] = position
        await self.state_manager.set(f'position_{token}', position)
        
    async def handle_profit_take(self, event: Event):
        """Handle profit taking requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        percentage = event.data.get('percentage', 25)
        
        if token in self.portfolio:
            await self.take_profit(token, percentage)
            
    async def update_allocations(self):
        """Update current allocations"""
        total_value = 0
        asset_values = {asset: 0 for asset in self.asset_classes}
        
        # Calculate current values
        for token, position in self.portfolio.items():
            asset_class = position.get('asset_class', 'small')
            value = position.get('value', 0)
            asset_values[asset_class] += value
            total_value += value
            
        # Calculate percentages
        if total_value > 0:
            for asset_class, value in asset_values.items():
                self.current_allocations[asset_class] = value / total_value
        else:
            self.current_allocations = {asset: 0 for asset in self.asset_classes}
            
        # Store allocations
        await self.state_manager.set('current_allocations', self.current_allocations)
        
    async def should_rebalance(self) -> bool:
        """Check if rebalancing is needed"""
        if not self.current_allocations:
            return False
            
        # Check drift against targets
        for asset_class, target in self.target_allocations.items():
            current = self.current_allocations.get(asset_class, 0)
            drift = abs(current - target)
            
            if drift > self.rebalance_threshold:
                return True
                
        return False
        
    async def execute_rebalance(self):
        """Execute portfolio rebalancing"""
        logger.info("Executing portfolio rebalance...")
        
        # Calculate target allocations based on regime
        regime = await self.state_manager.get('current_regime', 'neutral')
        self.target_allocations = self.calculate_target_allocations(regime)
        
        # Generate rebalance actions
        actions = self.generate_actions()
        
        if actions:
            # Execute actions
            rebalance_data = {
                'actions': actions,
                'target_allocations': self.target_allocations,
                'current_allocations': self.current_allocations,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in history
            self.rebalance_history.append(rebalance_data)
            
            # Publish rebalance
            event = Event(
                event_type="rebalance_executed",
                data=rebalance_data,
                source=self.agent_id
            )
            await self.event_bus.publish(event)
            
            logger.info(f"Rebalanced: {len(actions)} actions")
            
    def calculate_target_allocations(self, regime: str) -> Dict[str, float]:
        """Calculate target allocations based on regime"""
        # Base allocations
        base = {
            'micro': 0.12,
            'small': 0.30,
            'mid': 0.40,
            'stable': 0.18
        }
        
        # Adjust by regime
        adjustments = {
            'bull': {'micro': 1.2, 'small': 1.1, 'mid': 1.0, 'stable': 0.5},
            'alt': {'micro': 1.5, 'small': 1.2, 'mid': 0.8, 'stable': 0.5},
            'accumulation': {'micro': 0.8, 'small': 1.0, 'mid': 1.1, 'stable': 1.2},
            'neutral': {'micro': 1.0, 'small': 1.0, 'mid': 1.0, 'stable': 1.0},
            'bear': {'micro': 0.5, 'small': 0.7, 'mid': 0.8, 'stable': 2.0},
            'crash': {'micro': 0.3, 'small': 0.4, 'mid': 0.5, 'stable': 3.0}
        }
        
        adj = adjustments.get(regime, adjustments['neutral'])
        
        # Calculate adjusted allocations
        total = 0
        adjusted = {}
        
        for asset, weight in base.items():
            adjusted[asset] = weight * adj.get(asset, 1.0)
            total += adjusted[asset]
            
        # Normalize to 100%
        for asset in adjusted:
            adjusted[asset] /= total
            
        return adjusted
        
    def generate_actions(self) -> List[Dict]:
        """Generate rebalance actions"""
        actions = []
        
        for asset_class, target in self.target_allocations.items():
            current = self.current_allocations.get(asset_class, 0)
            diff = target - current
            
            if abs(diff) > self.rebalance_threshold:
                actions.append({
                    'asset_class': asset_class,
                    'action': 'increase' if diff > 0 else 'decrease',
                    'amount': abs(diff),
                    'target': target,
                    'current': current
                })
                
        return actions
        
    async def check_profit_taking(self):
        """Check and execute profit taking"""
        for token, position in self.portfolio.items():
            pnl_percent = position.get('pnl_percent', 0)
            
            if pnl_percent > self.profit_take_threshold * 100:
                # Take profit
                percentage = min(25, pnl_percent / 4)  # Scale profit taking
                await self.take_profit(token, percentage)
                
    async def take_profit(self, token: str, percentage: float):
        """Execute profit taking on a position"""
        if token not in self.portfolio:
            return
            
        position = self.portfolio[token]
        current_value = position.get('value', 0)
        take_amount = current_value * (percentage / 100)
        
        # Execute profit taking
        profit_data = {
            'token': token,
            'percentage': percentage,
            'amount': take_amount,
            'remaining': current_value - take_amount,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update position
        self.portfolio[token]['value'] -= take_amount
        self.portfolio[token]['profit_taken'] = self.portfolio[token].get('profit_taken', 0) + take_amount
        
        # Publish profit taken
        event = Event(
            event_type="profit_taken",
            data=profit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
        logger.info(f"Profit taken on {token}: {percentage}% ({take_amount:.2f})")
        
    async def publish_rebalance_update(self):
        """Publish rebalance data update"""
        rebalance_data = {
            'current_allocations': self.current_allocations,
            'target_allocations': self.target_allocations,
            'rebalance_history': self.rebalance_history[-5:],
            'total_rebalances': len(self.rebalance_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="rebalance_update",
            data=rebalance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get rebalancer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'current_allocations': self.current_allocations,
            'target_allocations': self.target_allocations,
            'positions': len(self.portfolio),
            'rebalance_history': len(self.rebalance_history),
            'timestamp': datetime.now().isoformat()
        }
