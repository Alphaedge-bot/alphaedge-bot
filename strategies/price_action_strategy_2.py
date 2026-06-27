"""
AlphaEdge Strategy – Price Action Strategy 2
Engulfing pattern detection for trend reversals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy2:
    """
    Price Action Strategy 2
    Uses engulfing patterns for trend reversal signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_2"
        self.name = "Price Action Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.engulfing_body_ratio = 1.2
        self.volume_confirm = 1.2
        self.confirmation_bars = 2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        pattern = data.get('pattern', 'none')
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish engulfing
        if pattern == 'bullish_engulfing' and volume_ratio > self.volume_confirm:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(pattern, volume_ratio, price),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bearish engulfing
        elif pattern == 'bearish_engulfing' and volume_ratio > self.volume_confirm:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(pattern, volume_ratio, price),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for engulfing pattern without volume confirmation
        elif pattern in ['bullish_engulfing', 'bearish_engulfing']:
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
        
    def calculate_confidence(self, pattern: str, volume_ratio: float, price: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern strength
        if pattern in ['bullish_engulfing', 'bearish_engulfing']:
            confidence += 0.25
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.25
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
