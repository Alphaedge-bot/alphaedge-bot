"""
AlphaEdge Strategy – Technical TA Strategy 8
ADX trend strength and directional movement signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy8:
    """
    Technical TA Strategy 8
    Uses ADX for trend strength and directional movement
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_8"
        self.name = "Technical TA Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.adx_strong_threshold = 40
        self.adx_weak_threshold = 20
        self.di_plus_threshold = 25
        self.di_minus_threshold = 25
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        adx = data.get('adx', 0)
        di_plus = data.get('di_plus', 0)
        di_minus = data.get('di_minus', 0)
        
        # Check for strong bullish trend
        if adx > self.adx_strong_threshold and di_plus > self.di_plus_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(adx, di_plus, di_minus),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for strong bearish trend
        elif adx > self.adx_strong_threshold and di_minus > self.di_minus_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(adx, di_plus, di_minus),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for trend weakening
        elif adx < self.adx_weak_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'neutral',
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
        
    def calculate_confidence(self, adx: float, di_plus: float, di_minus: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # ADX strength
        if adx > 50:
            confidence += 0.3
        elif adx > 40:
            confidence += 0.15
            
        # DI spread
        di_spread = abs(di_plus - di_minus)
        if di_spread > 30:
            confidence += 0.2
        elif di_spread > 20:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'adx_strong_threshold': self.adx_strong_threshold,
            'adx_weak_threshold': self.adx_weak_threshold
        }
