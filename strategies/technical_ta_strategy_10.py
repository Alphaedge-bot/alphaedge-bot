"""
AlphaEdge Strategy – Technical TA Strategy 10
Parabolic SAR trend reversal and trailing stop signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy10:
    """
    Technical TA Strategy 10
    Uses Parabolic SAR for trend reversal and trailing stops
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_10"
        self.name = "Technical TA Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.sar_step = 0.02
        self.sar_max_step = 0.2
        self.reversal_threshold = 0.01  # 1% confirmation
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        sar = data.get('sar', 0)
        trend = data.get('trend', 'neutral')
        
        # Check for bullish reversal
        if price > sar and trend != 'up':
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(price, sar, trend),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bearish reversal
        elif price < sar and trend != 'down':
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(price, sar, trend),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for trailing stop trigger
        elif price < sar * 0.98 and trend == 'up':
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': 0.8,
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
        
    def calculate_confidence(self, price: float, sar: float, trend: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Price vs SAR distance
        distance = abs(price - sar) / sar
        if distance > 0.03:
            confidence += 0.3
        elif distance > 0.01:
            confidence += 0.15
            
        # Trend reversal strength
        if trend in ['neutral', 'unknown']:
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
            'sar_step': self.sar_step,
            'sar_max_step': self.sar_max_step
        }
