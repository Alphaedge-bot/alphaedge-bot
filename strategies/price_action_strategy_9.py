"""
AlphaEdge Strategy – Price Action Strategy 9
Key level bounces and rejections
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy9:
    """
    Price Action Strategy 9
    Uses key level bounces and rejections
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_9"
        self.name = "Price Action Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.level_touch_threshold = 0.005  # 0.5%
        self.volume_confirm = 1.2
        self.level_strength = 3  # number of touches
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        support = data.get('support', 0)
        resistance = data.get('resistance', 0)
        support_touches = data.get('support_touches', 0)
        resistance_touches = data.get('resistance_touches', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for support bounce (buy)
        if support > 0 and abs(price - support) / support < self.level_touch_threshold:
            if support_touches >= self.level_strength and volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, support, support_touches, volume_ratio, 'support'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for resistance rejection (sell)
        elif resistance > 0 and abs(price - resistance) / resistance < self.level_touch_threshold:
            if resistance_touches >= self.level_strength and volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, resistance, resistance_touches, volume_ratio, 'resistance'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for level touch without volume confirmation
        elif support > 0 or resistance > 0:
            if (support > 0 and abs(price - support) / support < self.level_touch_threshold * 2) or \
               (resistance > 0 and abs(price - resistance) / resistance < self.level_touch_threshold * 2):
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
        
    def calculate_confidence(self, price: float, level: float, touches: int, volume_ratio: float, level_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Level strength
        if touches >= 5:
            confidence += 0.3
        elif touches >= 4:
            confidence += 0.2
        elif touches >= 3:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        # Price proximity
        proximity = abs(price - level) / level
        if proximity < 0.002:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
