"""
AlphaEdge Strategy – Profit Optimization Strategy 3
Trailing profit optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy3:
    """
    Profit Optimization Strategy 3
    Optimizes trailing profit levels
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_3"
        self.name = "Profit Optimization Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.trailing_pct = 0.05  # 5%
        self.activation_pct = 0.10  # 10%
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
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_price > 0:
            gain = (price - entry_price) / entry_price
            
            # Check if trailing stop should be activated
            if gain >= self.activation_pct:
                trailing_stop = highest_price * (1 - self.trailing_pct)
                
                # Check if trailing stop is hit
                if price <= trailing_stop:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'trailing_exit',
                            'confidence': self.calculate_confidence(gain),
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
        
    def calculate_confidence(self, gain: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain level
        if gain > 0.20:
            confidence += 0.2
        elif gain > 0.15:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'trailing_pct': self.trailing_pct,
            'activation_pct': self.activation_pct
        }
