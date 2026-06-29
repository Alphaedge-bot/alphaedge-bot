"""
AlphaEdge Strategy – HFT Micro Strategy 5
High-frequency order flow analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class HFTMicroStrategiesStrategy5:
    """
    HFT Micro Strategy 5
    Analyzes high-frequency order flow
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "hft_micro_strategies_5"
        self.name = "HFT Micro Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.order_flow_threshold = 0.3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        order_flow = data.get('order_flow', 0)
        flow_velocity = data.get('flow_velocity', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high-frequency order flow
        if order_flow > self.order_flow_threshold:
            if flow_velocity > 0:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'hft_flow',
                        'confidence': self.calculate_confidence(order_flow, flow_velocity),
                        'order_flow': order_flow,
                        'flow_velocity': flow_velocity,
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
        
    def calculate_confidence(self, order_flow: float, flow_velocity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Order flow
        if order_flow > 0.5:
            confidence += 0.2
        elif order_flow > 0.3:
            confidence += 0.1
            
        # Flow velocity
        if flow_velocity > 0.5:
            confidence += 0.2
        elif flow_velocity > 0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'order_flow_threshold': self.order_flow_threshold
        }
