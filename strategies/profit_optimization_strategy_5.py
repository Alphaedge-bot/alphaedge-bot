"""
AlphaEdge Strategy – Profit Optimization Strategy 5
Profit target adjustment based on market conditions
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy5:
    """
    Profit Optimization Strategy 5
    Adjusts profit targets based on market conditions
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_5"
        self.name = "Profit Optimization Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.base_target = 0.20  # 20%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        volatility = data.get('volatility', 0)
        momentum = data.get('momentum', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Adjust profit target based on market conditions
        adjusted_target = self.base_target
        
        # Volatility adjustment
        if volatility > 0.03:
            adjusted_target *= 1.2
        elif volatility < 0.01:
            adjusted_target *= 0.8
            
        # Momentum adjustment
        if momentum > 0:
            adjusted_target *= 1.1
        else:
            adjusted_target *= 0.9
            
        # Check for adjustment opportunity
        if abs(adjusted_target - self.base_target) > 0.02:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'adjust_target',
                    'confidence': self.calculate_confidence(volatility, momentum),
                    'adjusted_target': adjusted_target,
                    'original_target': self.base_target,
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
    async def handle_signal_request(self, event: Event):
        """Handle signal requests"""
        signal = {
            'strategy': self.strategy_id,
            'type': 'neutral',
            'confidence': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="signal_response",
            data=signal,
            source=self.strategy_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    def calculate_confidence(self, volatility: float, momentum: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Volatility
        if volatility > 0.05:
            confidence += 0.2
        elif volatility > 0.03:
            confidence += 0.1
            
        # Momentum
        if momentum > 0.5:
            confidence += 0.2
        elif momentum > 0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'base_target': self.base_target
        }
