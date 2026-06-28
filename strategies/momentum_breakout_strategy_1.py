"""
AlphaEdge Strategy – Momentum Breakout Strategy 1
Price momentum breakout detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy1:
    """
    Momentum Breakout Strategy 1
    Detects price momentum breakouts
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_1"
        self.name = "Momentum Breakout Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.momentum_threshold = 0.03  # 3%
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
        resistance = data.get('resistance', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_price > 0:
            momentum = (price - prev_price) / prev_price
            
            # Check for momentum breakout
            if momentum > self.momentum_threshold:
                if resistance > 0 and price > resistance * (1 + self.breakout_threshold):
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'momentum_breakout',
                            'confidence': self.calculate_confidence(momentum, price, resistance),
                            'momentum': momentum,
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
        
    def calculate_confidence(self, momentum: float, price: float, resistance: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Momentum
        if momentum > 0.05:
            confidence += 0.2
        elif momentum > 0.03:
            confidence += 0.1
            
        # Breakout strength
        if resistance > 0:
            breakout_pct = (price - resistance) / resistance
            if breakout_pct > 0.03:
                confidence += 0.2
            elif breakout_pct > 0.02:
                confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'momentum_threshold': self.momentum_threshold,
            'breakout_threshold': self.breakout_threshold
        }
