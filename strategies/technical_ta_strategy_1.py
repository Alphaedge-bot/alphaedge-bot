"""
AlphaEdge Strategy – Technical TA Strategy 1
RSI-based reversal detection and entry signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy1:
    """
    Technical TA Strategy 1
    Uses RSI to detect reversals and entry signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_1"
        self.name = "Technical TA Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_divergence_threshold = 5
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        rsi = data.get('rsi', 50)
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        
        # Check for oversold conditions
        if rsi <= self.rsi_oversold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(rsi, price, volume),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for overbought conditions
        elif rsi >= self.rsi_overbought:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(rsi, price, volume),
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
        
    def calculate_confidence(self, rsi: float, price: float, volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # RSI extreme confidence
        if rsi < 20 or rsi > 80:
            confidence += 0.3
        elif rsi < 25 or rsi > 75:
            confidence += 0.15
            
        # Volume confirmation
        if volume > 0:
            # Higher volume = higher confidence
            confidence += 0.2
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought
        }
