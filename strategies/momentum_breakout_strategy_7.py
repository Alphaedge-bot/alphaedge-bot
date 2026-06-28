"""
AlphaEdge Strategy – Momentum Breakout Strategy 7
Breakout with moving average momentum confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy7:
    """
    Momentum Breakout Strategy 7
    Confirms breakouts with moving average momentum
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_7"
        self.name = "Momentum Breakout Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.ma_breakout_threshold = 0.02  # 2%
        self.ma_momentum_threshold = 0.01  # 1%
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
        ma_20 = data.get('ma_20', 0)
        ma_50 = data.get('ma_50', 0)
        ma_slope = data.get('ma_slope', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if ma_20 > 0 and ma_50 > 0:
            ma_breakout = (price - ma_20) / ma_20
            
            # Check for MA breakout with momentum
            if ma_breakout > self.ma_breakout_threshold:
                if ma_slope > self.ma_momentum_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'ma_breakout',
                            'confidence': self.calculate_confidence(ma_breakout, ma_slope),
                            'ma_breakout': ma_breakout,
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
        
    def calculate_confidence(self, ma_breakout: float, ma_slope: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # MA breakout
        if ma_breakout > 0.04:
            confidence += 0.2
        elif ma_breakout > 0.02:
            confidence += 0.1
            
        # MA slope
        if ma_slope > 0.02:
            confidence += 0.2
        elif ma_slope > 0.01:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'ma_breakout_threshold': self.ma_breakout_threshold,
            'ma_momentum_threshold': self.ma_momentum_threshold
        }
