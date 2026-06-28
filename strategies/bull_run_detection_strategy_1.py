"""
AlphaEdge Strategy – Bull Run Detection Strategy 1
Parabolic trend detection and identification
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BullRunDetectionStrategy1:
    """
    Bull Run Detection Strategy 1
    Detects and identifies parabolic trends
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bull_run_detection_1"
        self.name = "Bull Run Detection Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.parabolic_threshold = 0.03  # 3%
        self.acceleration_threshold = 0.5
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
        prev_price = data.get('prev_price', price)
        acceleration = data.get('acceleration', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_price > 0:
            price_change = (price - prev_price) / prev_price
            
            # Check for parabolic move
            if price_change > self.parabolic_threshold:
                if acceleration > self.acceleration_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'bull_run_detected',
                            'confidence': self.calculate_confidence(price_change, acceleration),
                            'price_change': price_change,
                            'acceleration': acceleration,
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
        
    def calculate_confidence(self, price_change: float, acceleration: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Price change
        if price_change > 0.05:
            confidence += 0.2
        elif price_change > 0.03:
            confidence += 0.1
            
        # Acceleration
        if acceleration > 1.0:
            confidence += 0.2
        elif acceleration > 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'parabolic_threshold': self.parabolic_threshold,
            'acceleration_threshold': self.acceleration_threshold
        }
