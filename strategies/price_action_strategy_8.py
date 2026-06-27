"""
AlphaEdge Strategy – Price Action Strategy 8
Breakout retest and confirmation patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy8:
    """
    Price Action Strategy 8
    Uses breakout retest and confirmation patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_8"
        self.name = "Price Action Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.retest_threshold = 0.01  # 1%
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
        price = data.get('price', 0)
        breakout_level = data.get('breakout_level', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        retest_bars = data.get('retest_bars', 0)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish retest (buy)
        if breakout_level > 0 and price > breakout_level * (1 - self.retest_threshold):
            if price < breakout_level and volume_ratio > self.volume_confirm:
                if retest_bars > 0:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(price, breakout_level, volume_ratio, retest_bars),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for bearish retest (sell)
        elif breakout_level > 0 and price < breakout_level * (1 + self.retest_threshold):
            if price > breakout_level and volume_ratio > self.volume_confirm:
                if retest_bars > 0:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(price, breakout_level, volume_ratio, retest_bars),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for potential retest (watch)
        elif breakout_level > 0 and abs(price - breakout_level) / breakout_level < self.retest_threshold * 2:
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
        
    def calculate_confidence(self, price: float, level: float, volume_ratio: float, retest_bars: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Retest confirmation
        if retest_bars >= 2:
            confidence += 0.2
        elif retest_bars >= 1:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        # Price proximity
        proximity = abs(price - level) / level
        if proximity < 0.005:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
