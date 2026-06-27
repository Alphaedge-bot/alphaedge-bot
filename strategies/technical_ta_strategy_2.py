"""
AlphaEdge Strategy – Technical TA Strategy 2
MACD crossover momentum detection and trend following
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy2:
    """
    Technical TA Strategy 2
    Uses MACD crossovers for momentum and trend following
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_2"
        self.name = "Technical TA Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.macd_trigger_threshold = 0.1
        self.trend_strength_threshold = 1.5
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        macd = data.get('macd', {})
        macd_line = macd.get('macd_line', 0)
        signal_line = macd.get('signal_line', 0)
        histogram = macd.get('histogram', 0)
        
        # Check for bullish crossover
        if macd_line > signal_line and histogram > self.macd_trigger_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(macd_line, signal_line, histogram),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bearish crossover
        elif macd_line < signal_line and histogram < -self.macd_trigger_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(macd_line, signal_line, histogram),
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
        
    def calculate_confidence(self, macd_line: float, signal_line: float, histogram: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # MACD divergence strength
        divergence = abs(macd_line - signal_line)
        if divergence > 0.5:
            confidence += 0.3
        elif divergence > 0.2:
            confidence += 0.15
            
        # Histogram strength
        if abs(histogram) > 0.3:
            confidence += 0.2
        elif abs(histogram) > 0.1:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'macd_trigger_threshold': self.macd_trigger_threshold
        }
