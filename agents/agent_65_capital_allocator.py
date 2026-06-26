"""
AlphaEdge Agent 65 – Capital Allocator
Dynamic capital by regime, auto-rebalance on regime change, season allocation
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CapitalAllocator:
    """Capital Allocator – Dynamic capital allocation based on market conditions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "capital_allocator"
        self.running = False
        
        # Allocation state
        self.allocation_plan = {}
        self.regime_allocation = {}
        self.season_allocation = {}
        self.allocation_history = []
        
        # Configuration
        self.config = {
            'base_allocation': {
                'micro_cap': 0.10,
                'small_cap': 0.30,
                'mid_cap': 0.40,
                'stable': 0.20
            },
            'max_allocation': 0.80,
            'min_allocation': 0.10,
            'rebalance_threshold': 0.05,  # 5% drift
            'season_adjustment_factor': 0.2
        }
        
    async def start(self):
        """Start the capital allocator"""
        logger.info("Capital Allocator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("allocation_request", self.handle_allocation_request)
        await self.event_bus.subscribe("regime_change", self.handle_regime_change)
        await self.event_bus.subscribe("season_update", self.handle_season_update)
        
        # Start allocation cycle
        asyncio.create_task(self.run_allocation_cycle())
        
        logger.info("Capital Allocator running")
        
    async def stop(self):
        """Stop the capital allocator"""
        self.running = False
        logger.info("Capital Allocator stopped")
        
    async def run_allocation_cycle(self):
        """Run regular allocation cycle"""
        while self.running:
            try:
                # Update allocations
                await self.update_allocations()
                
                # Check rebalance
                await self.check_rebalance()
                
                # Publish allocation update
                await self.publish_allocation_update()
                
            except Exception as e:
                logger.error(f"Allocation cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_allocation_request(self, event: Event):
        """Handle allocation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        capital = event.data.get('capital')
        
        # Calculate allocation
        result = await self.calculate_allocation(capital)
        
        response = Event(
            event_type="allocation_response",
            data={
                'request_id': request_id,
                'capital': capital,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_regime_change(self, event: Event):
        """Handle regime change events"""
        if not self.running:
            return
            
        new_regime = event.data.get('regime')
        confidence = event.data.get('confidence', 0.5)
        
        logger.info(f"Regime change detected: {new_regime}")
        
        # Update allocation plan
        await self.update_regime_allocation(new_regime, confidence)
        
    async def handle_season_update(self, event: Event):
        """Handle season update events"""
        if not self.running:
            return
            
        season = event.data.get('season')
        positions = event.data.get('positions')
        
        logger.info(f"Season update: {season}")
        
        # Update season allocation
        await self.update_season_allocation(season, positions)
        
    async def update_allocations(self):
        """Update allocation plan"""
        # Get current regime and season
        regime = await self.state_manager.get('current_regime', 'neutral')
        season = await self.state_manager.get('current_season', 'balanced')
        
        # Calculate allocation
        allocation = await self.calculate_allocation(
            await self.state_manager.get('total_capital', 10000)
        )
        
        # Store allocation plan
        self.allocation_plan = allocation
        
        # Store in state
        await self.state_manager.set('allocation_plan', allocation)
        
    async def calculate_allocation(self, capital: float) -> Dict:
        """Calculate optimal allocation"""
        # Get current regime and season
        regime = await self.state_manager.get('current_regime', 'neutral')
        season = await self.state_manager.get('current_season', 'balanced')
        
        # Base allocation
        base = self.config['base_allocation']
        
        # Adjust for regime
        regime_multipliers = {
            'bull': {'micro': 1.2, 'small': 1.1, 'mid': 1.0, 'stable': 0.5},
            'alt': {'micro': 1.5, 'small': 1.2, 'mid': 0.8, 'stable': 0.5},
            'accumulation': {'micro': 0.8, 'small': 1.0, 'mid': 1.1, 'stable': 1.2},
            'neutral': {'micro': 1.0, 'small': 1.0, 'mid': 1.0, 'stable': 1.0},
            'bear': {'micro': 0.5, 'small': 0.7, 'mid': 0.8, 'stable': 2.0},
            'crash': {'micro': 0.3, 'small': 0.4, 'mid': 0.5, 'stable': 3.0}
        }
        
        regime_mult = regime_multipliers.get(regime, regime_multipliers['neutral'])
        
        # Adjust for season
        season_multipliers = {
            'micro_season': {'micro': 2.0, 'small': 0.8, 'mid': 0.8},
            'small_season': {'micro': 0.8, 'small': 2.0, 'mid': 0.8},
            'mid_season': {'micro': 0.8, 'small': 0.8, 'mid': 2.0},
            'balanced': {'micro': 1.0, 'small': 1.0, 'mid': 1.0}
        }
        
        season_mult = season_multipliers.get(season, season_multipliers['balanced'])
        
        # Calculate adjusted allocations
        total = 0
        adjusted = {}
        
        for category, weight in base.items():
            # Apply regime and season adjustments
            if category in regime_mult:
                weight *= regime_mult[category]
            if category in season_mult:
                weight *= season_mult[category]
            adjusted[category] = weight
            total += weight
            
        # Normalize
        for category in adjusted:
            adjusted[category] /= total
            
        # Apply min/max
        for category in adjusted:
            adjusted[category] = max(
                self.config['min_allocation'],
                min(self.config['max_allocation'], adjusted[category])
            )
            
        # Re-normalize
        total = sum(adjusted.values())
        for category in adjusted:
            adjusted[category] /= total
            
        # Calculate amounts
        amounts = {}
        for category, pct in adjusted.items():
            amounts[category] = capital * pct
            
        return {
            'percentages': adjusted,
            'amounts': amounts,
            'regime': regime,
            'season': season,
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_regime_allocation(self, regime: str, confidence: float):
        """Update allocation based on regime"""
        logger.info(f"Updating regime allocation: {regime} ({confidence:.2f})")
        
        # Calculate new allocation
        capital = await self.state_manager.get('total_capital', 10000)
        allocation = await self.calculate_allocation(capital)
        
        # Store regime allocation
        self.regime_allocation = {
            'regime': regime,
            'confidence': confidence,
            'allocation': allocation,
            'timestamp': datetime.now().isoformat()
        }
        
        # Trigger rebalance
        await self.check_rebalance(force=True)
        
    async def update_season_allocation(self, season: str, positions: Dict):
        """Update allocation based on season"""
        logger.info(f"Updating season allocation: {season}")
        
        # Store season allocation
        self.season_allocation = {
            'season': season,
            'positions': positions,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update allocation plan
        await self.update_allocations()
        
    async def check_rebalance(self, force: bool = False):
        """Check if rebalancing is needed"""
        # Get current allocation
        current = await self.state_manager.get('current_allocation', {})
        target = await self.calculate_allocation(
            await self.state_manager.get('total_capital', 10000)
        )
        
        if not current:
            await self.execute_rebalance(target)
            return
            
        # Check drift
        drift = {}
        for category in target['percentages']:
            current_pct = current.get('percentages', {}).get(category, 0)
            target_pct = target['percentages'].get(category, 0)
            drift[category] = target_pct - current_pct
            
        # Check if rebalance needed
        max_drift = max(abs(d) for d in drift.values())
        
        if force or max_drift > self.config['rebalance_threshold']:
            await self.execute_rebalance(target)
            
    async def execute_rebalance(self, target: Dict):
        """Execute rebalancing"""
        logger.info("Executing rebalancing...")
        
        # Generate rebalance actions
        current = await self.state_manager.get('current_allocation', {})
        actions = []
        
        for category, target_pct in target['percentages'].items():
            current_pct = current.get('percentages', {}).get(category, 0)
            diff = target_pct - current_pct
            
            if abs(diff) > 0.01:  # 1% threshold
                actions.append({
                    'category': category,
                    'action': 'increase' if diff > 0 else 'decrease',
                    'amount': abs(diff),
                    'target': target_pct,
                    'current': current_pct
                })
                
        # Store actions
        await self.state_manager.set('rebalance_actions', actions)
        
        # Update current allocation
        await self.state_manager.set('current_allocation', target)
        self.allocation_history.append({
            'target': target,
            'actions': actions,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Rebalancing completed: {len(actions)} actions")
        
    async def publish_allocation_update(self):
        """Publish allocation data update"""
        allocation_data = {
            'allocation_plan': self.allocation_plan,
            'regime_allocation': self.regime_allocation,
            'season_allocation': self.season_allocation,
            'allocation_history': self.allocation_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="capital_allocation_update",
            data=allocation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get capital allocator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'allocation_plan': self.allocation_plan,
            'regime_allocation': self.regime_allocation,
            'season_allocation': self.season_allocation,
            'allocation_history': len(self.allocation_history),
            'timestamp': datetime.now().isoformat()
        }
