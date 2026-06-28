"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 2
Scaled profit taking based on market conditions
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy2:
    """
    Profit Taking Strategies Strategy 2
    Scales profit taking based on market conditions
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_2"
        self.name = "Profit Taking Strategies Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.base_scale = 0.25  # 25%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        gain = data.get('gain', 0)
        volatility = data.get('volatility', 0)
        momentum = data.get('momentum', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate scale based on market conditions
        scale = self.base_scale
        
        # Adjust for gain
        if gain > 0.3:
            scale *= 1.5
        elif gain > 0.2:
            scale *= 1.2
            
        # Adjust for volatility
        if volatility > 0.03:
            scale *= 1.3
        elif volatility < 0.01:
            scale *= 0.8
            
        # Adjust for momentum
        if momentum > 0:
            scale *= 1.1
        else:
            scale *= 0.9
            
        # Check if taking profit is optimal
        if gain > 0.1:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'scaled_take_profit',
                    'confidence': self.calculate_confidence(gain, scale),
                    'scale': scale,
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
        
    def calculate_confidence(self, gain: float, scale: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain
        if gain > 0.2:
            confidence += 0.2
        elif gain > 0.1:
            confidence += 0.1
            
        # Scale
        if scale > 0.3:
            confidence += 0.2
        elif scale > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'base_scale': self.base_scale
        }
