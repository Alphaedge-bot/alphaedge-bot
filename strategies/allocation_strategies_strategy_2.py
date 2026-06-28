"""
AlphaEdge Strategy – Allocation Strategies Strategy 2
Risk-based allocation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AllocationStrategiesStrategy2:
    """
    Allocation Strategies Strategy 2
    Bases allocation on risk metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "allocation_strategies_2"
        self.name = "Allocation Strategies Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.risk_allocation = {
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
        risk_level = data.get('risk_level', 'medium')
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if risk level is valid
        if risk_level in self.risk_allocation:
            allocation = self.risk_allocation[risk_level]
            
            if allocation > 0.01:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'risk_allocate',
                        'confidence': self.calculate_confidence(risk_level, allocation),
                        'allocation': allocation,
                        'risk_level': risk_level,
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
        
    def calculate_confidence(self, risk_level: str, allocation: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Risk level
        if risk_level == 'low':
            confidence += 0.2
        elif risk_level == 'medium':
            confidence += 0.15
        elif risk_level == 'high':
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
            'risk_allocation': self.risk_allocation
        }
