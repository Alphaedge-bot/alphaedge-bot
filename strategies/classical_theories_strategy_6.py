"""
AlphaEdge Strategy – Classical Theories Strategy 6
Livermore key price levels and pivot points
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ClassicalTheoriesStrategy6:
    """
    Classical Theories Strategy 6
    Uses Livermore key price levels and pivot points
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "classical_theories_6"
        self.name = "Classical Theories Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.pivot_threshold = 0.005  # 0.5%
        self.key_level_count = 3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        price = data.get('price', 0)
        pivot_high = data.get('pivot_high', 0)
        pivot_low = data.get('pivot_low', 0)
        key_levels = data.get('key_levels', [])
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for breakout above pivot high
        if pivot_high > 0 and price > pivot_high * (1 + self.pivot_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, pivot_high, pivot_low, volume_ratio),
                    'pivot_high': pivot_high,
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for breakdown below pivot low
        elif pivot_low > 0 and price < pivot_low * (1 - self.pivot_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, pivot_high, pivot_low, volume_ratio),
                    'pivot_low': pivot_low,
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for key level bounce
        for level in key_levels[:self.key_level_count]:
            if abs(price - level) / level < self.pivot_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'watch',
                        'confidence': 0.5,
                        'key_level': level,
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
        
    def calculate_confidence(self, price: float, pivot_high: float, pivot_low: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pivot strength
        if pivot_high > 0:
            confidence += 0.2
        if pivot_low > 0:
            confidence += 0.1
            
        # Price distance
        if pivot_high > 0:
            distance = abs(price - pivot_high) / pivot_high
            if distance > 0.02:
                confidence += 0.1
                
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
            'pivot_threshold': self.pivot_threshold,
            'key_level_count': self.key_level_count
        }
