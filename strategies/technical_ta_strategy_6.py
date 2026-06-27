"""
AlphaEdge Strategy – Technical TA Strategy 6
Support and resistance breakout detection with volume confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy6:
    """
    Technical TA Strategy 6
    Uses support/resistance breakouts with volume confirmation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_6"
        self.name = "Technical TA Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.breakout_threshold = 0.02  # 2% above resistance
        self.volume_confirmation = 1.3  # 30% above average
        self.retest_threshold = 0.01    # 1% retest
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        resistance = data.get('resistance', 0)
        support = data.get('support', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma_20', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for resistance breakout (bullish)
        if resistance > 0 and price > resistance * (1 + self.breakout_threshold):
            if volume_ratio > self.volume_confirmation:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, resistance, volume_ratio),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for support breakdown (bearish)
        elif support > 0 and price < support * (1 - self.breakout_threshold):
            if volume_ratio > self.volume_confirmation:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, support, volume_ratio),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for retest (confirmation)
        elif resistance > 0 and price > resistance * (1 - self.retest_threshold):
            if price < resistance and volume_ratio > 1:
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
        
    def calculate_confidence(self, price: float, level: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout strength
        breakout_pct = abs(price - level) / level
        if breakout_pct > 0.05:
            confidence += 0.3
        elif breakout_pct > 0.02:
            confidence += 0.15
            
        # Volume confirmation
        if volume_ratio > 2.0:
            confidence += 0.2
        elif volume_ratio > 1.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'breakout_threshold': self.breakout_threshold,
            'volume_confirmation': self.volume_confirmation
        }
