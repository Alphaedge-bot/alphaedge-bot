"""
AlphaEdge Agent 62 – Position Sizer Optimizer
Dynamic sizing (2-6%), pyramiding (+20%/+50%/+100%/+200%), maximize return
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


class PositionSizer:
    """Position Sizer – Dynamic position sizing and pyramiding optimizer"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "position_sizer"
        self.running = False
        
        # Sizing state
        self.position_sizes = {}
        self.pyramid_levels = {}
        self.risk_metrics = {}
        
        # Configuration
        self.config = {
            'min_position_size': 0.02,  # 2%
            'max_position_size': 0.06,  # 6%
            'pyramid_increments': [0.20, 0.50, 1.00, 2.00],  # 20%, 50%, 100%, 200%
            'risk_per_trade': 0.02,  # 2% risk
            'max_pyramid_positions': 4,
            'volatility_adjustment': True
        }
        
    async def start(self):
        """Start the position sizer"""
        logger.info("Position Sizer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("sizing_request", self.handle_sizing_request)
        await self.event_bus.subscribe("pyramid_request", self.handle_pyramid_request)
        await self.event_bus.subscribe("risk_metrics_request", self.handle_risk_metrics_request)
        
        # Start sizing cycle
        asyncio.create_task(self.run_sizing_cycle())
        
        logger.info("Position Sizer running")
        
    async def stop(self):
        """Stop the position sizer"""
        self.running = False
        logger.info("Position Sizer stopped")
        
    async def run_sizing_cycle(self):
        """Run regular sizing cycle"""
        while self.running:
            try:
                # Update risk metrics
                await self.update_risk_metrics()
                
                # Optimize position sizes
                await self.optimize_position_sizes()
                
                # Update pyramid levels
                await self.update_pyramid_levels()
                
                # Publish sizer update
                await self.publish_sizer_update()
                
            except Exception as e:
                logger.error(f"Sizing cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_sizing_request(self, event: Event):
        """Handle sizing requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        position = event.data.get('position')
        
        # Calculate optimal size
        result = await self.calculate_position_size(position)
        
        response = Event(
            event_type="sizing_response",
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
        current_price = event.data.get('current_price')
        
        # Generate pyramid plan
        result = await self.generate_pyramid_plan(position, current_price)
        
        response = Event(
            event_type="pyramid_sizing_response",
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
        
    async def handle_risk_metrics_request(self, event: Event):
        """Handle risk metrics requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="risk_metrics_response",
            data={
                'risk_metrics': self.risk_metrics,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def update_risk_metrics(self):
        """Update risk metrics"""
        # In production, use actual risk calculations
        # For now, simulate
        
        # Get portfolio data
        positions = await self.state_manager.get('positions', [])
        total_capital = await self.state_manager.get('total_capital', 10000)
        
        # Calculate risk metrics
        var_95 = 0
        var_99 = 0
        expected_shortfall = 0
        
        if positions:
            # Simulate risk calculations
            var_95 = random.uniform(0.01, 0.05)
            var_99 = random.uniform(0.02, 0.08)
            expected_shortfall = random.uniform(0.02, 0.06)
            
        self.risk_metrics = {
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall': expected_shortfall,
            'risk_score': self.calculate_risk_score(var_95, var_99),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in state
        await self.state_manager.set('risk_metrics', self.risk_metrics)
        
    def calculate_risk_score(self, var_95: float, var_99: float) -> float:
        """Calculate overall risk score (0-100)"""
        base_score = 50
        
        # Adjust for VaR
        if var_95 > 0.04:
            base_score += 20
        elif var_95 > 0.02:
            base_score += 10
            
        if var_99 > 0.06:
            base_score += 20
        elif var_99 > 0.03:
            base_score += 10
            
        return min(100, base_score)
        
    async def optimize_position_sizes(self):
        """Optimize position sizes"""
        # Get current positions
        positions = await self.state_manager.get('positions', [])
        
        for position in positions:
            token = position.get('token')
            
            # Calculate optimal size
            size = await self.calculate_position_size(position)
            
            # Store size
            self.position_sizes[token] = size
            
            # Update state
            await self.state_manager.set(f'position_size_{token}', size)
            
    async def calculate_position_size(self, position: Dict) -> Dict:
        """Calculate optimal position size"""
        # Get risk parameters
        volatility = position.get('volatility', 0.3)
        confidence = position.get('confidence', 0.5)
        capital = await self.state_manager.get('total_capital', 10000)
        
        # Base size
        base_size = self.config['min_position_size']
        
        # Adjust for confidence
        confidence_adjustment = 1 + (confidence - 0.5) * 2  # 0-2 range
        
        # Adjust for volatility (inverse)
        if self.config['volatility_adjustment']:
            volatility_adjustment = 1 / (1 + volatility * 2)
        else:
            volatility_adjustment = 1
            
        # Calculate size
        size = base_size * confidence_adjustment * volatility_adjustment
        
        # Ensure within limits
        size = max(self.config['min_position_size'], 
                   min(self.config['max_position_size'], size))
        
        # Adjust for bull run
        bull_run = await self.state_manager.get('bull_run_confidence', 30) / 100
        if bull_run > 0.6:
            size *= 1.2  # 20% increase in bull run
            
        # Calculate actual dollar amount
        amount = capital * size
        
        return {
            'size': size,
            'amount': amount,
            'volatility': volatility,
            'confidence': confidence,
            'bull_run_adjustment': bull_run > 0.6,
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_pyramid_levels(self):
        """Update pyramid levels"""
        # Get current positions
        positions = await self.state_manager.get('positions', [])
        
        for position in positions:
            token = position.get('token')
            current_price = position.get('current_price', 0)
            
            # Generate pyramid plan
            plan = await self.generate_pyramid_plan(position, current_price)
            
            if plan and plan.get('recommended'):
                self.pyramid_levels[token] = plan
                await self.state_manager.set(f'pyramid_plan_{token}', plan)
                
    async def generate_pyramid_plan(self, position: Dict, current_price: float) -> Dict:
        """Generate pyramiding plan"""
        token = position.get('token')
        entry_price = position.get('entry_price', 0)
        position_size = position.get('size', 0)
        
        if entry_price <= 0:
            return {'recommended': False, 'reason': 'Invalid entry price'}
            
        # Calculate gain
        gain = (current_price - entry_price) / entry_price
        
        # Determine if pyramiding is appropriate
        if gain < 0.10:  # Need at least 10% gain
            return {'recommended': False, 'reason': 'Gain too small'}
            
        # Check risk score
        risk_score = self.risk_metrics.get('risk_score', 50)
        if risk_score > 70:
            return {'recommended': False, 'reason': 'Risk score too high'}
            
        # Generate pyramid levels
        levels = []
        current_size = position_size
        
        for i, increment in enumerate(self.config['pyramid_increments']):
            if i >= self.config['max_pyramid_positions']:
                break
                
            target_price = entry_price * (1 + increment)
            
            # Skip if target already reached
            if current_price >= target_price:
                # Calculate additional size
                additional_size = position_size * (increment / 2)
                current_size += additional_size
                
                levels.append({
                    'level': i + 1,
                    'target_price': target_price,
                    'additional_size': additional_size,
                    'total_size': current_size,
                    'increment': increment
                })
                
        if not levels:
            return {'recommended': False, 'reason': 'No pyramid levels reached'}
            
        return {
            'recommended': True,
            'current_gain': gain,
            'levels': levels,
            'total_size': current_size,
            'risk_score': risk_score,
            'timestamp': datetime.now().isoformat()
        }
        
    async def publish_sizer_update(self):
        """Publish sizer data update"""
        sizer_data = {
            'position_sizes': self.position_sizes,
            'pyramid_levels': self.pyramid_levels,
            'risk_metrics': self.risk_metrics,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="sizer_update",
            data=sizer_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get position sizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'position_sizes': len(self.position_sizes),
            'pyramid_levels': len(self.pyramid_levels),
            'risk_metrics': self.risk_metrics,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
