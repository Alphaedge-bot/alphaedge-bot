"""
AlphaEdge Strategy – Technical TA Strategy 22
Mean reversion with Bollinger Bands and RSI
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy22:
    """
    Technical TA Strategy 22
    Uses mean reversion with Bollinger Bands and RSI
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_22"
        self.name = "Technical TA Strategy 22"
        self.active = True
        
        # Strategy parameters
        self.bb_period = 20
        self.bb_std = 2.0
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        bb_lower = data.get('bb_lower', 0)
        bb_upper = data.get('bb_upper', 0)
        bb_middle = data.get('bb_middle', 0)
        rsi = data.get('rsi', 50)
        
        # Check for oversold mean reversion (buy)
        if price < bb_lower and rsi < self.rsi_oversold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(price, bb_lower, rsi, 'bullish'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for overbought mean reversion (sell)
        elif price > bb_upper and rsi > self.rsi_overbought:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(price, bb_upper, rsi, 'bearish'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for band touch with no confirmation (watch)
        elif price < bb_lower or price > bb_upper:
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
        
    def calculate_confidence(self, price: float, band: float, rsi: float, direction: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Band distance
        band_distance = abs(price - band) / band
        if band_distance > 0.03:
            confidence += 0.2
        elif band_distance > 0.02:
            confidence += 0.1
            
        # RSI extreme
        if direction == 'bullish':
            if rsi < 20:
                confidence += 0.3
            elif rsi < 30:
                confidence += 0.15
        else:  # bearish
            if rsi > 80:
                confidence += 0.3
            elif rsi > 70:
                confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'bb_period': self.bb_period,
            'bb_std': self.bb_std
        }
