"""
AlphaEdge Strategy – Technical TA Strategy 5
Volume analysis and accumulation/distribution signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy5:
    """
    Technical TA Strategy 5
    Uses volume analysis for accumulation/distribution signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_5"
        self.name = "Technical TA Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.volume_ma_period = 20
        self.volume_spike_threshold = 1.5  # 50% above average
        self.accumulation_threshold = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma_20', 1)
        price = data.get('price', 0)
        price_change = data.get('price_change', 0)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for accumulation (high volume + price increasing)
        if volume_ratio > self.accumulation_threshold and price_change > 0:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(volume_ratio, price_change, volume),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for distribution (high volume + price decreasing)
        elif volume_ratio > self.accumulation_threshold and price_change < 0:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(volume_ratio, price_change, volume),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for volume spike with price breakout
        elif volume_ratio > self.volume_spike_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': 0.5,
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
        
    def calculate_confidence(self, volume_ratio: float, price_change: float, volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Volume ratio confidence
        if volume_ratio > 2.0:
            confidence += 0.3
        elif volume_ratio > 1.5:
            confidence += 0.15
            
        # Price movement confirmation
        if abs(price_change) > 2.0:
            confidence += 0.2
        elif abs(price_change) > 1.0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'volume_ma_period': self.volume_ma_period,
            'volume_spike_threshold': self.volume_spike_threshold
        }
