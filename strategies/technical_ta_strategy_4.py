"""
AlphaEdge Strategy – Technical TA Strategy 4
Bollinger Bands breakout and volatility-based signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy4:
    """
    Technical TA Strategy 4
    Uses Bollinger Bands for breakout and volatility signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_4"
        self.name = "Technical TA Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.bb_period = 20
        self.bb_std = 2.0
        self.breakout_threshold = 0.02  # 2% above/below bands
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        bb_upper = data.get('bb_upper', 0)
        bb_lower = data.get('bb_lower', 0)
        bb_middle = data.get('bb_middle', 0)
        volatility = data.get('volatility', 0)
        
        # Check for upper band breakout (bullish)
        if price > bb_upper * (1 + self.breakout_threshold):
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(price, bb_upper, bb_middle, volatility),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for lower band breakout (bearish)
        elif price < bb_lower * (1 - self.breakout_threshold):
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(price, bb_lower, bb_middle, volatility),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for volatility contraction (potential breakout)
        elif volatility < 0.1:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': 0.3,
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
        
    def calculate_confidence(self, price: float, band: float, middle: float, volatility: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout strength
        breakout_pct = abs(price - band) / band
        if breakout_pct > 0.05:
            confidence += 0.3
        elif breakout_pct > 0.02:
            confidence += 0.15
            
        # Band width (volatility confirmation)
        band_width = abs(band - middle) / middle
        if band_width > 0.1:
            confidence += 0.2
        elif band_width > 0.05:
            confidence += 0.1
            
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
