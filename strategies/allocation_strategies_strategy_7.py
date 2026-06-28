"""
AlphaEdge Strategy – Allocation Strategies Strategy 7
Correlation-based allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy7:
    """
    Allocation Strategies Strategy 7
    Bases allocation on correlation metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_7"
        self.name = "Allocation Strategies Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.correlation_allocation = {
            'low': 0.06,
            'medium': 0.04,
            'high': 0.02,
            'extreme': 0.01
        }
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        correlation_level = data.get('correlation_level', 'medium')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if correlation level is valid
        if correlation_level in self.correlation_allocation:
            allocation = self.correlation_allocation[correlation_level]
            
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'correlation_allocate',
                    'confidence': self.calculate_confidence(correlation_level, allocation),
                    'allocation': allocation,
                    'correlation_level': correlation_level,
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
        
    def calculate_confidence(self, correlation_level: str, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Correlation level
        if correlation_level == 'low':
            confidence += 0.2
        elif correlation_level == 'medium':
            confidence += 0.15
        elif correlation_level == 'high':
            confidence += 0.1
            
        # Allocation
        if allocation > 0.04:
            confidence += 0.2
        elif allocation > 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'correlation_allocation': self.correlation_allocation
        }
