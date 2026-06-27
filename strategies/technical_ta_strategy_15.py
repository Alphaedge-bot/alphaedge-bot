"""
AlphaEdge Strategy – Technical TA Strategy 15
Market structure analysis (higher highs/lower lows)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy15:
    """
    Technical TA Strategy 15
    Uses market structure for trend identification
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_15"
        self.name = "Technical TA Strategy 15"
        self.active = True
        
        # Strategy parameters
        self.structure_window = 20
        self.hh_hh_threshold = 0.01  # 1%
        self.break_threshold = 0.015  # 1.5%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        struct_type = data.get('structure_type', 'neutral')
        prev_high = data.get('prev_high', price)
        prev_low = data.get('prev_low', price)
        
        # Check for bullish structure (higher high, higher low)
        if struct_type == 'bullish':
            if price > prev_high:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, prev_high, prev_low, 'bullish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish structure (lower high, lower low)
        elif struct_type == 'bearish':
            if price < prev_low:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, prev_high, prev_low, 'bearish'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for structure break
        elif struct_type == 'breakout':
            if price > prev_high * (1 + self.break_threshold):
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': 0.7,
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
        
    def calculate_confidence(self, price: float, prev_high: float, prev_low: float, structure: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Structure strength
        if structure == 'bullish':
            hh_hh_pct = (price - prev_high) / prev_high
            if hh_hh_pct > 0.02:
                confidence += 0.3
            elif hh_hh_pct > 0.01:
                confidence += 0.15
                
        else:  # bearish
            ll_ll_pct = (prev_low - price) / prev_low
            if ll_ll_pct > 0.02:
                confidence += 0.3
            elif ll_ll_pct > 0.01:
                confidence += 0.15
            
        # Structure range
        range_pct = (prev_high - prev_low) / prev_low
        if range_pct > 0.03:
            confidence += 0.2
        elif range_pct > 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'structure_window': self.structure_window
        }
