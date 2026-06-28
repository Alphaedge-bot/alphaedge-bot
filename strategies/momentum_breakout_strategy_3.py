"""
AlphaEdge Strategy – Momentum Breakout Strategy 3
Acceleration-based momentum breakout
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy3:
    """
    Momentum Breakout Strategy 3
    Detects acceleration-based momentum breakouts
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_3"
        self.name = "Momentum Breakout Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.acceleration_threshold = 0.5
        self.breakout_threshold = 0.02  # 2%
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
        resistance = data.get('resistance', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_price > 0 and resistance > 0:
            momentum = (price - prev_price) / prev_price
            breakout_pct = (price - resistance) / resistance
            
            # Check for acceleration breakout
            if acceleration > self.acceleration_threshold:
                if breakout_pct > self.breakout_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'acceleration_breakout',
                            'confidence': self.calculate_confidence(acceleration, breakout_pct, momentum),
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
        
    def calculate_confidence(self, acceleration: float, breakout_pct: float, momentum: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Acceleration
        if acceleration > 1.0:
            confidence += 0.2
        elif acceleration > 0.5:
            confidence += 0.1
            
        # Breakout
        if breakout_pct > 0.03:
            confidence += 0.2
        elif breakout_pct > 0.02:
            confidence += 0.1
            
        # Momentum
        if momentum > 0.03:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'acceleration_threshold': self.acceleration_threshold,
            'breakout_threshold': self.breakout_threshold
        }
