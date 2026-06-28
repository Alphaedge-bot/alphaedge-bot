"""
AlphaEdge Strategy – Bull Run Detection Strategy 3
New ATH breakout detection and confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BullRunDetectionStrategy3:
    """
    Bull Run Detection Strategy 3
    Detects and confirms new ATH breakouts
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bull_run_detection_3"
        self.name = "Bull Run Detection Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.ath_breakout_threshold = 0.01  # 1%
        self.confirmation_bars = 3
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
        ath_price = data.get('ath_price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if ath_price > 0:
            ath_breakout = (price - ath_price) / ath_price
            
            # Check for ATH breakout
            if ath_breakout > self.ath_breakout_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'ath_breakout_detected',
                        'confidence': self.calculate_confidence(ath_breakout, volume_ratio),
                        'ath_breakout': ath_breakout,
                        'ath_price': ath_price,
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
        
    def calculate_confidence(self, ath_breakout: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # ATH breakout
        if ath_breakout > 0.03:
            confidence += 0.2
        elif ath_breakout > 0.01:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'ath_breakout_threshold': self.ath_breakout_threshold,
            'confirmation_bars': self.confirmation_bars
        }
