"""
AlphaEdge Strategy – Allocation Strategies Strategy 8
Momentum-based allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy8:
    """
    Allocation Strategies Strategy 8
    Bases allocation on momentum metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_8"
        self.name = "Allocation Strategies Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.momentum_allocation = {
            'strong': 0.06,
            'moderate': 0.04,
            'weak': 0.02,
            'negative': 0.01
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
        momentum_level = data.get('momentum_level', 'moderate')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if momentum level is valid
        if momentum_level in self.momentum_allocation:
            allocation = self.momentum_allocation[momentum_level]
            
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'momentum_allocate',
                    'confidence': self.calculate_confidence(momentum_level, allocation),
                    'allocation': allocation,
                    'momentum_level': momentum_level,
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
        
    def calculate_confidence(self, momentum_level: str, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Momentum level
        if momentum_level == 'strong':
            confidence += 0.2
        elif momentum_level == 'moderate':
            confidence += 0.15
        elif momentum_level == 'weak':
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
            'momentum_allocation': self.momentum_allocation
        }
