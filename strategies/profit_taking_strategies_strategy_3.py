"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 3
Trailing profit taking based on momentum
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy3:
    """
    Profit Taking Strategies Strategy 3
    Uses trailing profit taking based on momentum
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_3"
        self.name = "Profit Taking Strategies Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.trailing_activation = 0.10  # 10%
        self.trailing_step = 0.02  # 2%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        price = data.get('price', 0)
        entry_price = data.get('entry_price', 0)
        highest_price = data.get('highest_price', entry_price)
        momentum = data.get('momentum', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_price > 0 and highest_price > 0:
            gain = (price - entry_price) / entry_price
            peak_gain = (highest_price - entry_price) / entry_price
            
            # Check if trailing should be activated
            if gain >= self.trailing_activation:
                # Calculate trailing stop based on momentum
                momentum_factor = 1 + (momentum * 0.5)
                trailing_stop = peak_gain * (1 - self.trailing_step * momentum_factor)
                
                # Check if trailing stop is hit
                if gain <= trailing_stop:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'trailing_take_profit',
                            'confidence': self.calculate_confidence(gain, peak_gain),
                            'trailing_stop': trailing_stop,
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
        
    def calculate_confidence(self, gain: float, peak_gain: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain vs peak
        gain_ratio = gain / peak_gain if peak_gain > 0 else 0
        if gain_ratio < 0.8:
            confidence += 0.2
        elif gain_ratio < 0.9:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'trailing_activation': self.trailing_activation,
            'trailing_step': self.trailing_step
        }
