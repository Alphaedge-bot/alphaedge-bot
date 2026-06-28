"""
AlphaEdge Strategy – Momentum Breakout Strategy 2
Volume breakout with momentum confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy2:
    """
    Momentum Breakout Strategy 2
    Detects volume breakouts with momentum confirmation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_2"
        self.name = "Momentum Breakout Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.volume_spike_threshold = 2.0  # 2x normal
        self.momentum_threshold = 0.02  # 2%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        price = data.get('price', 0)
        prev_price = data.get('prev_price', price)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_price > 0:
            momentum = (price - prev_price) / prev_price
            
            # Check for volume breakout with momentum
            if volume_ratio > self.volume_spike_threshold:
                if momentum > self.momentum_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'volume_breakout',
                            'confidence': self.calculate_confidence(volume_ratio, momentum),
                            'volume_ratio': volume_ratio,
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
        
    def calculate_confidence(self, volume_ratio: float, momentum: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Volume spike
        if volume_ratio > 3.0:
            confidence += 0.2
        elif volume_ratio > 2.0:
            confidence += 0.1
            
        # Momentum
        if momentum > 0.05:
            confidence += 0.2
        elif momentum > 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'volume_spike_threshold': self.volume_spike_threshold,
            'momentum_threshold': self.momentum_threshold
        }
