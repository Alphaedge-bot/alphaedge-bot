"""
AlphaEdge Strategy – Price Action Strategy 5
Fakeout and false breakout detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy5:
    """
    Price Action Strategy 5
    Uses fakeout and false breakout detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_5"
        self.name = "Price Action Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.fakeout_threshold = 0.015  # 1.5%
        self.confirmation_bars = 3
        self.volume_spike_threshold = 1.3
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        high = data.get('high', price)
        low = data.get('low', price)
        prev_high = data.get('prev_high', high)
        prev_low = data.get('prev_low', low)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish fakeout (break above then reverse)
        if price < prev_high and high > prev_high * (1 + self.fakeout_threshold):
            if volume_ratio > self.volume_spike_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, high, prev_high, volume_ratio, 'bullish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish fakeout (break below then reverse)
        elif price > prev_low and low < prev_low * (1 - self.fakeout_threshold):
            if volume_ratio > self.volume_spike_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, low, prev_low, volume_ratio, 'bearish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for fakeout with no reversal
        elif (price < prev_high and high > prev_high) or (price > prev_low and low < prev_low):
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
        
    def calculate_confidence(self, price: float, extreme: float, level: float, volume_ratio: float, direction: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fakeout strength
        fakeout_pct = abs(extreme - level) / level
        if fakeout_pct > 0.02:
            confidence += 0.2
        elif fakeout_pct > 0.015:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
