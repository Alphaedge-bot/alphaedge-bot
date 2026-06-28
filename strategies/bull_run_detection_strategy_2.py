"""
AlphaEdge Strategy – Bull Run Detection Strategy 2
Alt season detection and identification
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BullRunDetectionStrategy2:
    """
    Bull Run Detection Strategy 2
    Detects and identifies alt seasons
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bull_run_detection_2"
        self.name = "Bull Run Detection Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.alt_performance_threshold = 0.1  # 10%
        self.btc_dominance_threshold = 0.05  # 5%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        alt_performance = data.get('alt_performance', 0)
        btc_dominance = data.get('btc_dominance', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for alt season conditions
        if alt_performance > self.alt_performance_threshold:
            if btc_dominance < (1 - self.btc_dominance_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'alt_season_detected',
                        'confidence': self.calculate_confidence(alt_performance, btc_dominance),
                        'alt_performance': alt_performance,
                        'btc_dominance': btc_dominance,
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
        
    def calculate_confidence(self, alt_performance: float, btc_dominance: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Alt performance
        if alt_performance > 0.2:
            confidence += 0.2
        elif alt_performance > 0.1:
            confidence += 0.1
            
        # BTC dominance drop
        if btc_dominance < 0.4:
            confidence += 0.2
        elif btc_dominance < 0.45:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'alt_performance_threshold': self.alt_performance_threshold,
            'btc_dominance_threshold': self.btc_dominance_threshold
        }
