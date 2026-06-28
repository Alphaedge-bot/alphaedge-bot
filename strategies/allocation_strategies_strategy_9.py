"""
AlphaEdge Strategy – Allocation Strategies Strategy 9
Sector-based allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy9:
    """
    Allocation Strategies Strategy 9
    Bases allocation on sector performance
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_9"
        self.name = "Allocation Strategies Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.sector_allocation = {
            'defi': 0.06,
            'layer1': 0.05,
            'layer2': 0.04,
            'gaming': 0.03,
            'memes': 0.02,
            'other': 0.01
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
        sector = data.get('sector', 'other')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if sector is valid
        if sector in self.sector_allocation:
            allocation = self.sector_allocation[sector]
            
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sector_allocate',
                    'confidence': self.calculate_confidence(sector, allocation),
                    'allocation': allocation,
                    'sector': sector,
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
        
    def calculate_confidence(self, sector: str, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sector
        if sector == 'defi':
            confidence += 0.2
        elif sector == 'layer1':
            confidence += 0.15
        elif sector == 'layer2':
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
            'sector_allocation': self.sector_allocation
        }
