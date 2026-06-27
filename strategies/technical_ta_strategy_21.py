"""
AlphaEdge Strategy – Technical TA Strategy 21
Time-based cycles and seasonality patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy21:
    """
    Technical TA Strategy 21
    Uses time-based cycles and seasonality patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_21"
        self.name = "Technical TA Strategy 21"
        self.active = True
        
        # Strategy parameters
        self.day_of_week_weights = {
            0: 1.0,  # Monday
            1: 1.1,  # Tuesday
            2: 1.2,  # Wednesday
            3: 1.1,  # Thursday
            4: 0.9,  # Friday
            5: 0.7,  # Saturday
            6: 0.7   # Sunday
        }
        self.month_weights = {
            1: 1.0, 2: 0.9, 3: 1.1, 4: 1.0,
            5: 1.1, 6: 0.9, 7: 1.0, 8: 1.1,
            9: 0.9, 10: 1.1, 11: 0.9, 12: 1.0
        }
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        now = datetime.now()
        day_weight = self.day_of_week_weights.get(now.weekday(), 1.0)
        month_weight = self.month_weights.get(now.month, 1.0)
        
        # Check for strong day/month combination (buy)
        if day_weight > 1.1 and month_weight > 1.0:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(day_weight, month_weight),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for weak day/month combination (sell)
        elif day_weight < 0.9 and month_weight < 1.0:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(day_weight, month_weight),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for end of month/start of month effects
        elif now.day <= 3 or now.day >= 28:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': 0.4,
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
        
    def calculate_confidence(self, day_weight: float, month_weight: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Day weight confidence
        if day_weight > 1.2:
            confidence += 0.2
        elif day_weight > 1.1:
            confidence += 0.1
            
        # Month weight confidence
        if month_weight > 1.1:
            confidence += 0.2
        elif month_weight > 1.0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
