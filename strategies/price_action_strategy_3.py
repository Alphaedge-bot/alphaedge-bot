"""
AlphaEdge Strategy – Price Action Strategy 3
Inside bar and breakout patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy3:
    """
    Price Action Strategy 3
    Uses inside bars and breakout patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_3"
        self.name = "Price Action Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.inside_bar_breakout = 0.01  # 1%
        self.volume_confirm = 1.2
        
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
        high = data.get('high', price)
        low = data.get('low', price)
        prev_high = data.get('prev_high', high)
        prev_low = data.get('prev_low', low)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish inside bar breakout
        if pattern == 'inside_bar':
            if price > prev_high and volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(pattern, volume_ratio, price, prev_high),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish inside bar breakdown
            elif price < prev_low and volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(pattern, volume_ratio, price, prev_low),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for inside bar with no breakout
        elif pattern == 'inside_bar':
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
        
    def calculate_confidence(self, pattern: str, volume_ratio: float, price: float, level: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern strength
        if pattern == 'inside_bar':
            confidence += 0.2
            
        # Breakout strength
        breakout_pct = abs(price - level) / level
        if breakout_pct > 0.02:
            confidence += 0.2
        elif breakout_pct > 0.01:
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
