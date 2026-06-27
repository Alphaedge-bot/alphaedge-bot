"""
AlphaEdge Strategy – Technical TA Strategy 11
Pivot point support/resistance with breakout signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy11:
    """
    Technical TA Strategy 11
    Uses pivot points for support/resistance breakout signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_11"
        self.name = "Technical TA Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.breakout_threshold = 0.01  # 1%
        self.pivot_strength_threshold = 2  # number of touches
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        pivot_high = data.get('pivot_high', 0)
        pivot_low = data.get('pivot_low', 0)
        pivot_strength = data.get('pivot_strength', 0)
        
        # Check for resistance breakout
        if pivot_high > 0 and price > pivot_high * (1 + self.breakout_threshold):
            if pivot_strength >= self.pivot_strength_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, pivot_high, pivot_strength),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for support breakdown
        elif pivot_low > 0 and price < pivot_low * (1 - self.breakout_threshold):
            if pivot_strength >= self.pivot_strength_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, pivot_low, pivot_strength),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for pivot bounce
        elif pivot_low > 0 and price > pivot_low * (1 + self.breakout_threshold * 0.5):
            if pivot_strength >= self.pivot_strength_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': 0.6,
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
        
    def calculate_confidence(self, price: float, pivot: float, strength: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout strength
        breakout_pct = abs(price - pivot) / pivot
        if breakout_pct > 0.02:
            confidence += 0.2
        elif breakout_pct > 0.01:
            confidence += 0.1
            
        # Pivot strength
        if strength >= 4:
            confidence += 0.3
        elif strength >= 3:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'breakout_threshold': self.breakout_threshold,
            'pivot_strength_threshold': self.pivot_strength_threshold
        }
