"""
AlphaEdge Strategy – Classical Theories Strategy 5
Fibonacci retracement and extension levels
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ClassicalTheoriesStrategy5:
    """
    Classical Theories Strategy 5
    Uses Fibonacci retracement and extension levels
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "classical_theories_5"
        self.name = "Classical Theories Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.fib_retracement = [0.236, 0.382, 0.500, 0.618, 0.786]
        self.fib_extension = [1.272, 1.618, 2.0, 2.618]
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
        fib_level = data.get('fib_level', 0)
        fib_type = data.get('fib_type', 'retracement')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for Fibonacci retracement bounce
        if fib_type == 'retracement' and fib_level > 0:
            if abs(price - fib_level) / fib_level < 0.01:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy' if price > fib_level else 'sell',
                        'confidence': self.calculate_confidence(fib_level, fib_type, volume_ratio),
                        'fib_level': fib_level,
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for Fibonacci extension target
        elif fib_type == 'extension' and fib_level > 0:
            if price > fib_level and volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'take_profit',
                    'confidence': self.calculate_confidence(fib_level, fib_type, volume_ratio),
                    'fib_level': fib_level,
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
        
    def calculate_confidence(self, fib_level: float, fib_type: str, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fibonacci level
        if fib_level in [0.618, 0.786, 1.618]:
            confidence += 0.2
        else:
            confidence += 0.1
            
        # Fibonacci type
        if fib_type == 'retracement':
            confidence += 0.1
        else:
            confidence += 0.05
            
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
            'fib_retracement': self.fib_retracement,
            'fib_extension': self.fib_extension
        }
