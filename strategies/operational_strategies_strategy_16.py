"""
AlphaEdge Strategy – Operational Strategies Strategy 16
User experience and interface optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OperationalStrategiesStrategy16:
    """
    Operational Strategies Strategy 16
    Optimizes user experience and interface
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "operational_strategies_16"
        self.name = "Operational Strategies Strategy 16"
        self.active = True
        
        # Strategy parameters
        self.ux_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        ux_score = data.get('ux_score', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for UX optimization opportunity
        if ux_score > self.ux_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'optimize_ux',
                    'confidence': self.calculate_confidence(ux_score),
                    'ux_score': ux_score,
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
        
    def calculate_confidence(self, ux_score: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # UX score
        if ux_score > 0.85:
            confidence += 0.3
        elif ux_score > 0.7:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'ux_threshold': self.ux_threshold
        }
