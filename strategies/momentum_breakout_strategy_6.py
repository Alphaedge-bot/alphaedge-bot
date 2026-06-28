"""
AlphaEdge Strategy – Momentum Breakout Strategy 6
Breakout retest and continuation pattern
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy6:
    """
    Momentum Breakout Strategy 6
    Identifies breakout retest and continuation patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_6"
        self.name = "Momentum Breakout Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.retest_threshold = 0.01  # 1%
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
        breakout_level = data.get('breakout_level', 0)
        retest_count = data.get('retest_count', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if breakout_level > 0:
            retest_proximity = abs(price - breakout_level) / breakout_level
            
            # Check for retest confirmation
            if retest_proximity < self.retest_threshold:
                if retest_count > 0:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'retest_breakout',
                            'confidence': self.calculate_confidence(retest_count, retest_proximity),
                            'retest_count': retest_count,
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
        
    def calculate_confidence(self, retest_count: int, retest_proximity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Retest count
        if retest_count > 2:
            confidence += 0.2
        elif retest_count > 0:
            confidence += 0.1
            
        # Retest proximity
        if retest_proximity < 0.005:
            confidence += 0.2
        elif retest_proximity < 0.01:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'retest_threshold': self.retest_threshold
        }
