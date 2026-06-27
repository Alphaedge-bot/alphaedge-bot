"""
AlphaEdge Strategy – Liquidation Cascade Strategy 4
Market depth and order book resilience analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LiquidationCascadeStrategy4:
    """
    Liquidation Cascade Strategy 4
    Analyzes market depth and order book resilience
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "liquidation_cascade_4"
        self.name = "Liquidation Cascade Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.depth_threshold = 100000  # $100K
        self.spread_threshold = 0.01   # 1%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bid_depth = data.get('bid_depth', 0)
        ask_depth = data.get('ask_depth', 0)
        spread = data.get('spread', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for low liquidity (sell)
        if bid_depth < self.depth_threshold and ask_depth < self.depth_threshold:
            if spread > self.spread_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(bid_depth, ask_depth, spread),
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
        
    def calculate_confidence(self, bid_depth: float, ask_depth: float, spread: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Depth
        if bid_depth < 50000 and ask_depth < 50000:
            confidence += 0.3
        elif bid_depth < 100000 and ask_depth < 100000:
            confidence += 0.15
            
        # Spread
        if spread > 0.02:
            confidence += 0.2
        elif spread > 0.01:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'depth_threshold': self.depth_threshold
        }
