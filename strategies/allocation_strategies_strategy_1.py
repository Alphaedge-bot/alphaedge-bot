"""
AlphaEdge Strategy – Allocation Strategies Strategy 1
Market cap weighted allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy1:
    """
    Allocation Strategies Strategy 1
    Uses market cap weighted allocation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_1"
        self.name = "Allocation Strategies Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.max_allocation = 0.06  # 6%
        self.min_allocation = 0.01  # 1%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        market_cap = data.get('market_cap', 0)
        total_market_cap = data.get('total_market_cap', 1)
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if total_market_cap > 0:
            # Calculate market cap weight
            weight = market_cap / total_market_cap
            
            # Calculate allocation
            allocation = self.min_allocation + (weight * (self.max_allocation - self.min_allocation))
            
            # Check if allocation is significant
            if allocation > self.min_allocation:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'allocate',
                        'confidence': self.calculate_confidence(weight, allocation),
                        'allocation': allocation,
                        'weight': weight,
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
        
    def calculate_confidence(self, weight: float, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Weight
        if weight > 0.05:
            confidence += 0.2
        elif weight > 0.02:
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
            'max_allocation': self.max_allocation,
            'min_allocation': self.min_allocation
        }
