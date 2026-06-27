"""
AlphaEdge Strategy – Price Action Strategy 10
Triple top/bottom pattern detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy10:
    """
    Price Action Strategy 10
    Uses triple top/bottom patterns for reversals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_10"
        self.name = "Price Action Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.pattern_threshold = 0.015  # 1.5%
        self.volume_confirm = 1.2
        self.confirmation_bars = 3
        
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
        pattern_level = data.get('pattern_level', 0)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for triple top (bearish reversal)
        if pattern == 'triple_top' and volume_ratio > self.volume_confirm:
            if price < pattern_level * (1 - self.pattern_threshold):
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(pattern, volume_ratio, price, pattern_level),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for triple bottom (bullish reversal)
        elif pattern == 'triple_bottom' and volume_ratio > self.volume_confirm:
            if price > pattern_level * (1 + self.pattern_threshold):
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(pattern, volume_ratio, price, pattern_level),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for pattern without volume confirmation
        elif pattern in ['triple_top', 'triple_bottom']:
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
        
    def calculate_confidence(self, pattern: str, volume_ratio: float, price: float, level: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern reliability
        if pattern in ['triple_top', 'triple_bottom']:
            confidence += 0.25
            
        # Breakout strength
        breakout_pct = abs(price - level) / level
        if breakout_pct > 0.02:
            confidence += 0.2
        elif breakout_pct > 0.015:
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
            'active': self.active
        }
