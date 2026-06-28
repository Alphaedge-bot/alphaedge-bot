"""
AlphaEdge Strategy – AlphaEdge Proprietary Strategy 6
AlphaEdge Market Microstructure (AMM)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlphaEdgeProprietaryStrategy6:
    """
    AlphaEdge Proprietary Strategy 6
    AlphaEdge Market Microstructure - Proprietary microstructure analysis
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "alphaedge_proprietary_6"
        self.name = "AlphaEdge Proprietary Strategy 6"
        self.active = True
        
        # Strategy parameters (Proprietary)
        self.spread_threshold = 0.005
        self.order_imbalance_threshold = 0.3
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
        order_imbalance = data.get('order_imbalance', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for microstructure opportunities
        if spread < self.spread_threshold:
            if abs(order_imbalance) > self.order_imbalance_threshold:
                if volume_ratio > self.volume_confirm:
                    # Determine direction from order imbalance
                    direction = 'buy' if order_imbalance > 0 else 'sell'
                    
                    signal = {
                        'strategy': self.strategy_id,
                        'type': direction,
                        'confidence': self.calculate_confidence(spread, abs(order_imbalance)),
                        'order_imbalance': order_imbalance,
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
        
    def calculate_confidence(self, spread: float, imbalance: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Spread
        if spread < 0.002:
            confidence += 0.2
        elif spread < 0.005:
            confidence += 0.1
            
        # Order imbalance
        if imbalance > 0.5:
            confidence += 0.2
        elif imbalance > 0.3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'spread_threshold': self.spread_threshold,
            'order_imbalance_threshold': self.order_imbalance_threshold
        }
