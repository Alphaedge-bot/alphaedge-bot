"""
AlphaEdge Strategy – Allocation Strategies Strategy 4
Performance-based allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy4:
    """
    Allocation Strategies Strategy 4
    Bases allocation on performance metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_4"
        self.name = "Allocation Strategies Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.performance_allocation = {
            'top': 0.06,
            'good': 0.04,
            'average': 0.03,
            'poor': 0.02
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
        performance_rank = data.get('performance_rank', 'average')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if rank is valid
        if performance_rank in self.performance_allocation:
            allocation = self.performance_allocation[performance_rank]
            
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'performance_allocate',
                    'confidence': self.calculate_confidence(performance_rank, allocation),
                    'allocation': allocation,
                    'performance_rank': performance_rank,
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
        
    def calculate_confidence(self, rank: str, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Rank
        if rank == 'top':
            confidence += 0.2
        elif rank == 'good':
            confidence += 0.15
        elif rank == 'average':
            confidence += 0.1
            
        # Allocation
        if allocation > 0.04:
            confidence += 0.2
        elif allocation > 0.03:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'performance_allocation': self.performance_allocation
        }
