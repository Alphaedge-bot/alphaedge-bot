"""
AlphaEdge Strategy – Technical TA Strategy 18
Gap detection and filling patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy18:
    """
    Technical TA Strategy 18
    Uses gap detection and filling patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_18"
        self.name = "Technical TA Strategy 18"
        self.active = True
        
        # Strategy parameters
        self.gap_threshold = 0.01  # 1% minimum gap
        self.gap_fill_threshold = 0.005  # 0.5% fill
        self.volume_confirm = 1.2  # 20% above average
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        prev_close = data.get('prev_close', price)
        open_price = data.get('open', price)
        high_price = data.get('high', price)
        low_price = data.get('low', price)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish breakaway gap
        if open_price > prev_close * (1 + self.gap_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, prev_close, open_price, 'bullish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish breakaway gap
        elif open_price < prev_close * (1 - self.gap_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, prev_close, open_price, 'bearish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for gap fill (bullish)
        elif price > prev_close and abs(price - prev_close) / prev_close < self.gap_fill_threshold:
            if volume_ratio > 1:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'watch',
                    'confidence': 0.5,
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
        
    def calculate_confidence(self, price: float, prev_close: float, open_price: float, direction: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gap size
        gap_size = abs(open_price - prev_close) / prev_close
        if gap_size > 0.02:
            confidence += 0.2
        elif gap_size > 0.015:
            confidence += 0.1
            
        # Gap direction
        if direction == 'bullish':
            if price > open_price:
                confidence += 0.2
            else:
                confidence += 0.1
        else:  # bearish
            if price < open_price:
                confidence += 0.2
            else:
                confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'gap_threshold': self.gap_threshold
        }
