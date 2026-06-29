"""
AlphaEdge Strategy – Robustness & Resilience Strategy 5
Resource exhaustion and overload protection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RobustnessResilienceStrategy5:
    """
    Robustness & Resilience Strategy 5
    Protects against resource exhaustion and overload
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "robustness_resilience_5"
        self.name = "Robustness & Resilience Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.resource_threshold = 0.7  # 70%
        self.overload_threshold = 0.8  # 80%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        resource_usage = data.get('resource_usage', 0)
        overload_risk = data.get('overload_risk', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for resource protection signal
        if resource_usage > self.resource_threshold:
            if overload_risk > self.overload_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'resource_protection',
                        'confidence': self.calculate_confidence(resource_usage, overload_risk),
                        'resource_usage': resource_usage,
                        'overload_risk': overload_risk,
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
        
    def calculate_confidence(self, resource_usage: float, overload_risk: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Resource usage
        if resource_usage > 0.85:
            confidence += 0.2
        elif resource_usage > 0.7:
            confidence += 0.1
            
        # Overload risk
        if overload_risk > 0.9:
            confidence += 0.2
        elif overload_risk > 0.8:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'resource_threshold': self.resource_threshold,
            'overload_threshold': self.overload_threshold
        }
