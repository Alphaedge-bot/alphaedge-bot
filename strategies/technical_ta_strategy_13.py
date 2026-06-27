"""
AlphaEdge Strategy – Technical TA Strategy 13
Candlestick pattern recognition (engulfing, hammer, etc.)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy13:
    """
    Technical TA Strategy 13
    Uses candlestick patterns for reversal signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_13"
        self.name = "Technical TA Strategy 13"
        self.active = True
        
        # Strategy parameters
        self.pattern_confidence = 0.6
        self.volume_confirmation = 1.2  # 20% above average
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        pattern = data.get('pattern', 'none')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish engulfing
        if pattern == 'bullish_engulfing':
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(pattern, volume_ratio),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bearish engulfing
        elif pattern == 'bearish_engulfing':
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(pattern, volume_ratio),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for hammer (bullish reversal)
        elif pattern == 'hammer':
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(pattern, volume_ratio),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for shooting star (bearish reversal)
        elif pattern == 'shooting_star':
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(pattern, volume_ratio),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for doji (indecision)
        elif pattern == 'doji':
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
        
    def calculate_confidence(self, pattern: str, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern reliability
        pattern_reliability = {
            'bullish_engulfing': 0.7,
            'bearish_engulfing': 0.7,
            'hammer': 0.65,
            'shooting_star': 0.65,
            'doji': 0.4
        }
        reliability = pattern_reliability.get(pattern, 0.5)
        confidence += (reliability - 0.5)
        
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pattern_confidence': self.pattern_confidence
        }
