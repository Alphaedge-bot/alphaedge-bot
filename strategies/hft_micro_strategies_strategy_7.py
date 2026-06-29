"""
AlphaEdge Strategy – HFT Micro Strategy 7
Spread capture and market making signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class HFTMicroStrategiesStrategy7:
    """
    HFT Micro Strategy 7
    Captures spread and market making signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "hft_micro_strategies_7"
        self.name = "HFT Micro Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.spread_threshold = 0.002  # 0.2%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        spread = data.get('spread', 0)
        market_depth = data.get('market_depth', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for spread capture signal
        if spread > self.spread_threshold:
            if market_depth > 0:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'spread_capture',
                        'confidence': self.calculate_confidence(spread, market_depth),
                        'spread': spread,
                        'market_depth': market_depth,
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
        
    def calculate_confidence(self, spread: float, market_depth: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Spread
        if spread > 0.005:
            confidence += 0.2
        elif spread > 0.002:
            confidence += 0.1
            
        # Market depth
        if market_depth > 0.5:
            confidence += 0.2
        elif market_depth > 0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'spread_threshold': self.spread_threshold
        }
