"""
AlphaEdge Strategy – Liquidation Cascade Strategy 3
Liquidation event detection and volume impact
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LiquidationCascadeStrategy3:
    """
    Liquidation Cascade Strategy 3
    Detects liquidation events and volume impact
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "liquidation_cascade_3"
        self.name = "Liquidation Cascade Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.liquidation_threshold = 100000  # $100K
        self.volume_spike_threshold = 2.0    # 2x normal
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        liquidation_events = data.get('liquidation_events', [])
        volume_spike = data.get('volume_spike', 1.0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for liquidation events
        if liquidation_events:
            total_liquidated = sum(e.get('amount', 0) for e in liquidation_events)
            
            if total_liquidated > self.liquidation_threshold:
                if volume_spike > self.volume_spike_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'buy',
                            'confidence': self.calculate_confidence(total_liquidated, volume_ratio),
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
        
    def calculate_confidence(self, liquidated: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Liquidation amount
        if liquidated > 500000:
            confidence += 0.3
        elif liquidated > 100000:
            confidence += 0.15
            
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
            'liquidation_threshold': self.liquidation_threshold
        }
