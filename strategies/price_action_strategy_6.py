"""
AlphaEdge Strategy – Price Action Strategy 6
Range consolidation breakouts and continuations
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy6:
    """
    Price Action Strategy 6
    Uses range consolidation breakouts and continuations
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_6"
        self.name = "Price Action Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.range_width_threshold = 0.02  # 2%
        self.breakout_threshold = 0.01  # 1%
        self.volume_confirm = 1.2
        self.min_range_bars = 5
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        range_high = data.get('range_high', 0)
        range_low = data.get('range_low', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        range_bars = data.get('range_bars', 0)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for valid range
        if range_bars >= self.min_range_bars and range_high > 0 and range_low > 0:
            range_width = (range_high - range_low) / range_high
            
            # Check for bullish range breakout
            if price > range_high * (1 + self.breakout_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(price, range_high, range_low, range_width, volume_ratio),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
            # Check for bearish range breakdown
            elif price < range_low * (1 - self.breakout_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(price, range_high, range_low, range_width, volume_ratio),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
            # Check for range breakout without volume confirmation
            elif price > range_high or price < range_low:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'watch',
                    'confidence': 0.4,
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
        
    def calculate_confidence(self, price: float, high: float, low: float, range_width: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Range width confirmation
        if range_width > 0.03:
            confidence += 0.2
        elif range_width > 0.02:
            confidence += 0.1
            
        # Breakout strength
        breakout_pct = abs(price - high) / high
        if breakout_pct > 0.02:
            confidence += 0.2
        elif breakout_pct > 0.01:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
