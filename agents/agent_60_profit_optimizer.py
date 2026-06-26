"""
AlphaEdge Agent 60 – Profit Optimizer
Dynamic take-profit, bull run trend detection (probabilistic), pyramiding optimizer
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizer:
    """Profit Optimizer – Dynamic profit optimization and position management"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "profit_optimizer"
        self.running = False
        
        # Optimization state
        self.take_profit_levels = {}
        self.pyramid_plans = {}
        self.bull_run_probability = 0.5
        
        # Configuration
        self.config = {
            'pyramid_increments': [0.20, 0.50, 1.00, 2.00],  # 20%, 50%, 100%, 200%
            'profit_target_multipliers': [1.15, 1.25, 1.40, 1.50],  # 15%, 25%, 40%, 50%
            'bull_run_threshold': 0.7,
            'max_pyramid_positions': 4,
            'position_size_multiplier': 1.5
        }
        
    async def start(self):
        """Start the profit optimizer"""
        logger.info("Profit Optimizer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("profit_optimization_request", self.handle_profit_optimization_request)
        await self.event_bus.subscribe("pyramid_request", self.handle_pyramid_request)
        await self.event_bus.subscribe("bull_run_check", self.handle_bull_run_check)
        
        # Start optimization cycle
        asyncio.create_task(self.run_optimization_cycle())
        
        logger.info("Profit Optimizer running")
        
    async def stop(self):
        """Stop the profit optimizer"""
        self.running = False
        logger.info("Profit Optimizer stopped")
        
    async def run_optimization_cycle(self):
        """Run regular optimization cycle"""
        while self.running:
            try:
                # Update bull run probability
                await self.update_bull_run_probability()
                
                # Optimize take-profit levels
                await self.optimize_take_profits()
                
                # Optimize pyramiding
                await self.optimize_pyramiding()
                
                # Publish optimizer update
                await self.publish_optimizer_update()
                
            except Exception as e:
                logger.error(f"Optimization cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_profit_optimization_request(self, event: Event):
        """Handle profit optimization requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        position = event.data.get('position')
        
        # Optimize profit for position
        result = await self.optimize_position_profit(position)
        
        response = Event(
            event_type="profit_optimization_response",
            data={
                'request_id': request_id,
                'position': position,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_pyramid_request(self, event: Event):
        """Handle pyramid requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        position = event.data.get('position')
        
        # Generate pyramid plan
        result = await self.generate_pyramid_plan(position)
        
        response = Event(
            event_type="pyramid_response",
            data={
                'request_id': request_id,
                'position': position,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_bull_run_check(self, event: Event):
        """Handle bull run checks"""
        if not self.running:
            return
            
        # Check if bull run is likely
        is_bull_run = self.bull_run_probability > self.config['bull_run_threshold']
        
        response = Event(
            event_type="bull_run_check_response",
            data={
                'is_bull_run': is_bull_run,
                'probability': self.bull_run_probability,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def update_bull_run_probability(self):
        """Update bull run probability"""
        # In production, use real market data
        # For now, simulate
        
        # Get market metrics
        momentum = await self.state_manager.get('market_momentum', 0.5)
        volume = await self.state_manager.get('market_volume', 0.5)
        sentiment = await self.state_manager.get('sentiment_score', 50) / 100
        
        # Calculate probability
        probability = (
            momentum * 0.4 +
            volume * 0.3 +
            sentiment * 0.3
        )
        
        # Add some noise
        probability += random.uniform(-0.05, 0.05)
        probability = max(0, min(1, probability))
        
        self.bull_run_probability = probability
        
        await self.state_manager.set('bull_run_probability', probability)
        
    async def optimize_take_profits(self):
        """Optimize take-profit levels"""
        # Get current positions
        positions = await self.state_manager.get('positions', [])
        
        for position in positions:
            token = position.get('token')
            entry_price = position.get('entry_price', 0)
            
            # Calculate optimal take-profit levels
            levels = []
            for i, multiplier in enumerate(self.config['profit_target_multipliers']):
                # Adjust based on bull run probability
                adjusted_mult = multiplier + (self.bull_run_probability * 0.2)
                levels.append({
                    'level': i + 1,
                    'price': entry_price * adjusted_mult,
                    'percentage': (adjusted_mult - 1) * 100,
                    'allocation': self.calculate_level_allocation(i)
                })
                
            self.take_profit_levels[token] = {
                'levels': levels,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in state
            await self.state_manager.set(f'take_profit_levels_{token}', levels)
            
    def calculate_level_allocation(self, level_index: int) -> float:
        """Calculate allocation for each take-profit level"""
        # Higher levels get smaller allocations
        allocations = [0.40, 0.30, 0.20, 0.10]  # 40%, 30%, 20%, 10%
        return allocations[level_index] if level_index < len(allocations) else 0.10
        
    async def optimize_pyramiding(self):
        """Optimize pyramiding strategy"""
        # Get current positions
        positions = await self.state_manager.get('positions', [])
        
        for position in positions:
            token = position.get('token')
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', entry_price)
            
            # Check if pyramiding is appropriate
            price_gain = (current_price - entry_price) / entry_price
            
            if price_gain > 0.10:  # 10% gain
                # Generate pyramid plan
                plan = await self.generate_pyramid_plan(position)
                self.pyramid_plans[token] = plan
                
                # Store in state
                await self.state_manager.set(f'pyramid_plan_{token}', plan)
                
    async def generate_pyramid_plan(self, position: Dict) -> Dict:
        """Generate pyramiding plan for a position"""
        token = position.get('token')
        entry_price = position.get('entry_price', 0)
        current_size = position.get('size', 0)
        
        # Check if pyramiding is appropriate
        if not await self.should_pyramid(position):
            return {'status': 'not_recommended'}
            
        # Generate plan
        plan = {
            'token': token,
            'entry_price': entry_price,
            'current_size': current_size,
            'increments': [],
            'target_sizes': [],
            'risk_level': self.calculate_risk_level(position)
        }
        
        # Calculate pyramid increments
        current_position = current_size
        for i, increment in enumerate(self.config['pyramid_increments']):
            if i >= self.config['max_pyramid_positions']:
                break
                
            # Calculate target price for this increment
            target_price = entry_price * (1 + increment)
            
            # Calculate additional size
            additional_size = current_size * (increment / 2)
            
            plan['increments'].append({
                'level': i + 1,
                'target_price': target_price,
                'additional_size': additional_size,
                'total_size': current_position + additional_size
            })
            
            current_position += additional_size
            
        return plan
        
    async def should_pyramid(self, position: Dict) -> bool:
        """Determine if pyramiding is recommended"""
        token = position.get('token')
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', entry_price)
        
        # Check price gain
        gain = (current_price - entry_price) / entry_price
        
        # Check bull run probability
        bull_run = self.bull_run_probability > self.config['bull_run_threshold']
        
        # Check volume trend
        volume_trend = await self.state_manager.get('volume_trend', 'stable')
        
        # Determine if pyramiding is recommended
        if gain > 0.15 and bull_run and volume_trend == 'increasing':
            return True
        elif gain > 0.25 and bull_run:
            return True
        else:
            return False
            
    def calculate_risk_level(self, position: Dict) -> str:
        """Calculate risk level for pyramiding"""
        # In production, use actual risk metrics
        # For now, simulate
        risk_factors = [
            position.get('volatility', 0.3),
            position.get('liquidity', 0.5),
            position.get('drawdown', 0.1)
        ]
        
        avg_risk = sum(risk_factors) / len(risk_factors)
        
        if avg_risk < 0.2:
            return 'low'
        elif avg_risk < 0.4:
            return 'medium'
        else:
            return 'high'
            
    async def optimize_position_profit(self, position: Dict) -> Dict:
        """Optimize profit for a specific position"""
        token = position.get('token')
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', entry_price)
        
        # Calculate current gain
        gain = (current_price - entry_price) / entry_price
        
        # Determine optimal take-profit
        if gain > 0.30:
            recommendation = 'take_profit'
            levels = self.take_profit_levels.get(token, {}).get('levels', [])
        elif gain > 0.10 and self.bull_run_probability > 0.6:
            recommendation = 'pyramid'
            plan = self.pyramid_plans.get(token, {})
        else:
            recommendation = 'hold'
            plan = None
            
        return {
            'token': token,
            'recommendation': recommendation,
            'gain': gain,
            'bull_run_probability': self.bull_run_probability,
            'levels': levels if recommendation == 'take_profit' else None,
            'plan': plan if recommendation == 'pyramid' else None,
            'timestamp': datetime.now().isoformat()
        }
        
    async def publish_optimizer_update(self):
        """Publish optimizer data update"""
        optimizer_data = {
            'bull_run_probability': self.bull_run_probability,
            'take_profit_levels': self.take_profit_levels,
            'pyramid_plans': self.pyramid_plans,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="profit_optimizer_update",
            data=optimizer_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get profit optimizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'bull_run_probability': self.bull_run_probability,
            'take_profit_levels': len(self.take_profit_levels),
            'pyramid_plans': len(self.pyramid_plans),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
