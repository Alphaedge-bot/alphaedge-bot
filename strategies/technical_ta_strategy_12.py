"""
AlphaEdge Strategy – Technical TA Strategy 12
Divergence detection (RSI, MACD, price) for reversal signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy12:
    """
    Technical TA Strategy 12
    Uses divergence detection for reversal signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_12"
        self.name = "Technical TA Strategy 12"
        self.active = True
        
        # Strategy parameters
        self.divergence_window = 10
        self.confirmation_threshold = 0.02  # 2%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        rsi = data.get('rsi', 50)
        macd_hist = data.get('macd_hist', 0)
        price_high = data.get('price_high', price)
        rsi_high = data.get('rsi_high', 50)
        price_low = data.get('price_low', price)
        rsi_low = data.get('rsi_low', 50)
        
        # Check for bearish divergence (price higher, RSI lower)
        if price_high > price and rsi < rsi_high:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(price, rsi, 'bearish'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bullish divergence (price lower, RSI higher)
        elif price_low < price and rsi > rsi_low:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(price, rsi, 'bullish'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for MACD divergence
        if macd_hist > 0 and price_high < price:
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
        
    def calculate_confidence(self, price: float, rsi: float, divergence_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # RSI divergence strength
        if divergence_type == 'bullish':
            if rsi < 30:
                confidence += 0.3
            elif rsi < 40:
                confidence += 0.15
        else:  # bearish
            if rsi > 70:
                confidence += 0.3
            elif rsi > 60:
                confidence += 0.15
            
        # Price confirmation
        if divergence_type == 'bullish':
            confidence += 0.2
        else:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'divergence_window': self.divergence_window
        }
