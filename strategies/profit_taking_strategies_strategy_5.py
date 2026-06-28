"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 5
Volatility-adjusted profit taking
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy5:
    """
    Profit Taking Strategies Strategy 5
    Adjusts profit taking based on volatility
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_5"
        self.name = "Profit Taking Strategies Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.base_gain = 0.15  # 15%
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
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Adjust target based on volatility
        volatility_factor = 1 + (volatility * 2)
        adjusted_target = self.base_gain * volatility_factor
        
        # Check if target is reached
        if gain >= adjusted_target:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'volatility_adjusted_take_profit',
                    'confidence': self.calculate_confidence(gain, adjusted_target),
                    'volatility': volatility,
                    'adjusted_target': adjusted_target,
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
        
    def calculate_confidence(self, gain: float, target: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain vs target
        gain_ratio = gain / target if target > 0 else 0
        if gain_ratio > 1.2:
            confidence += 0.2
        elif gain_ratio > 1.0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'base_gain': self.base_gain
        }
