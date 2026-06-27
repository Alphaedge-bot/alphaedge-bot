"""
AlphaEdge Strategy – Technical TA Strategy 7
Fibonacci retracement and extension levels
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy7:
    """
    Technical TA Strategy 7
    Uses Fibonacci retracement and extension levels
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_7"
        self.name = "Technical TA Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.fib_levels = [0.236, 0.382, 0.500, 0.618, 0.786]
        self.extension_levels = [1.272, 1.618, 2.000, 2.618]
        self.confirmation_threshold = 0.01  # 1% touch
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        swing_high = data.get('swing_high', 0)
        swing_low = data.get('swing_low', 0)
        
        if swing_high == 0 or swing_low == 0:
            return
            
        # Calculate Fibonacci levels
        diff = swing_high - swing_low
        
        for level in self.fib_levels:
            fib_level = swing_high - (diff * level)
            
            # Check for bounce at fib level
            if abs(price - fib_level) / fib_level < self.confirmation_threshold:
                if price > fib_level:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(level, price, fib_level),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                else:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(level, price, fib_level),
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
        
    def calculate_confidence(self, level: float, price: float, fib_level: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fibonacci level significance
        if level in [0.618, 0.786]:
            confidence += 0.3
        elif level in [0.382, 0.500]:
            confidence += 0.15
            
        # Price proximity to fib level
        proximity = abs(price - fib_level) / fib_level
        if proximity < 0.005:
            confidence += 0.2
        elif proximity < 0.01:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'fib_levels': self.fib_levels
        }
