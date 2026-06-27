"""
AlphaEdge Strategy – Technical TA Strategy 24
Keltner channels and volatility-based trading
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy24:
    """
    Technical TA Strategy 24
    Uses Keltner channels for volatility-based trading
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_24"
        self.name = "Technical TA Strategy 24"
        self.active = True
        
        # Strategy parameters
        self.keltner_ema_period = 20
        self.keltner_atr_multiplier = 1.5
        self.channel_threshold = 0.01  # 1%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        keltner_upper = data.get('keltner_upper', 0)
        keltner_lower = data.get('keltner_lower', 0)
        keltner_middle = data.get('keltner_middle', 0)
        volatility = data.get('volatility', 0)
        
        # Check for upper channel breakout (buy)
        if keltner_upper > 0 and price > keltner_upper:
            if volatility > 0.02:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, keltner_upper, keltner_lower, volatility),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for lower channel breakdown (sell)
        elif keltner_lower > 0 and price < keltner_lower:
            if volatility > 0.02:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, keltner_upper, keltner_lower, volatility),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for channel touch (watch)
        elif keltner_upper > 0 and keltner_lower > 0:
            if abs(price - keltner_upper) / keltner_upper < 0.005:
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
        
    def calculate_confidence(self, price: float, upper: float, lower: float, volatility: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Channel width
        channel_width = (upper - lower) / upper
        if channel_width > 0.06:
            confidence += 0.2
        elif channel_width > 0.04:
            confidence += 0.1
            
        # Volatility confirmation
        if volatility > 0.03:
            confidence += 0.2
        elif volatility > 0.02:
            confidence += 0.1
            
        # Price vs channel
        if price > upper or price < lower:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'keltner_ema_period': self.keltner_ema_period,
            'keltner_atr_multiplier': self.keltner_atr_multiplier
        }
