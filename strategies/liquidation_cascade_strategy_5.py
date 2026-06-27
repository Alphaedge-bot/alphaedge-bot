"""
AlphaEdge Strategy – Liquidation Cascade Strategy 5
Stop-loss clustering and trigger price analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LiquidationCascadeStrategy5:
    """
    Liquidation Cascade Strategy 5
    Analyzes stop-loss clustering and trigger prices
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "liquidation_cascade_5"
        self.name = "Liquidation Cascade Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.cluster_threshold = 1000  # contracts
        self.trigger_distance = 0.02   # 2%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        stop_cluster = data.get('stop_cluster', 0)
        trigger_distance = data.get('trigger_distance', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for stop cluster risk
        if stop_cluster > self.cluster_threshold:
            if trigger_distance < self.trigger_distance:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'watch',
                        'confidence': self.calculate_confidence(stop_cluster, trigger_distance),
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
        
    def calculate_confidence(self, cluster: float, distance: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Cluster size
        if cluster > 5000:
            confidence += 0.3
        elif cluster > 1000:
            confidence += 0.15
            
        # Trigger distance
        if distance < 0.01:
            confidence += 0.2
        elif distance < 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'cluster_threshold': self.cluster_threshold
        }
