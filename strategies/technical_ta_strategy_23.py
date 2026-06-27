"""
AlphaEdge Strategy – Technical TA Strategy 23
Donchian channels and breakout trading
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy23:
    """
    Technical TA Strategy 23
    Uses Donchian channels for breakout trading
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_23"
        self.name = "Technical TA Strategy 23"
        self.active = True
        
        # Strategy parameters
        self.donchian_period = 20
        self.breakout_threshold = 0.01  # 1%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        donchian_high = data.get('donchian_high', 0)
        donchian_low = data.get('donchian_low', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish breakout
        if donchian_high > 0 and price > donchian_high * (1 + self.breakout_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, donchian_high, donchian_low, volume_ratio),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish breakdown
        elif donchian_low > 0 and price < donchian_low * (1 - self.breakout_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, donchian_high, donchian_low, volume_ratio),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for channel tight (watch for breakout)
        elif donchian_high > 0 and donchian_low > 0:
            channel_range = (donchian_high - donchian_low) / donchian_high
            if channel_range < 0.02:  # Very tight channel
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
        
    def calculate_confidence(self, price: float, high: float, low: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout strength
        breakout_pct = abs(price - high) / high
        if breakout_pct > 0.02:
            confidence += 0.2
        elif breakout_pct > 0.01:
            confidence += 0.1
            
        # Channel width
        channel_width = (high - low) / high
        if channel_width > 0.05:
            confidence += 0.2
        elif channel_width > 0.03:
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
            'active': self.active,
            'donchian_period': self.donchian_period
        }
