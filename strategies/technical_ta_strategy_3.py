"""
AlphaEdge Strategy – Technical TA Strategy 3
Moving average crossover and trend identification
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy3:
    """
    Technical TA Strategy 3
    Uses moving average crossovers for trend identification
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_3"
        self.name = "Technical TA Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.ma_fast = 20
        self.ma_slow = 50
        self.ma_crossover_threshold = 0.5
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        ma_fast = data.get('ma_20', 0)
        ma_slow = data.get('ma_50', 0)
        price = data.get('price', 0)
        
        # Check for golden cross (bullish)
        if ma_fast > ma_slow and ma_fast > ma_slow * 1.005:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(ma_fast, ma_slow, price),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for death cross (bearish)
        elif ma_fast < ma_slow and ma_fast < ma_slow * 0.995:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(ma_fast, ma_slow, price),
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
        
    def calculate_confidence(self, ma_fast: float, ma_slow: float, price: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # MA crossover strength
        ma_diff = abs(ma_fast - ma_slow) / ma_slow * 100
        if ma_diff > 2.0:
            confidence += 0.3
        elif ma_diff > 1.0:
            confidence += 0.15
            
        # Price vs MA confirmation
        if price > ma_fast and price > ma_slow:
            confidence += 0.2
        elif price < ma_fast and price < ma_slow:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'ma_fast': self.ma_fast,
            'ma_slow': self.ma_slow
        }
