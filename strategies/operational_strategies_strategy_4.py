"""
AlphaEdge Strategy – Operational Strategies Strategy 4
Gas fee optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OperationalStrategiesStrategy4:
    """
    Operational Strategies Strategy 4
    Optimizes gas fees
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "operational_strategies_4"
        self.name = "Operational Strategies Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.gas_optimization_threshold = 0.3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        gas_price = data.get('gas_price', 0)
        avg_gas_price = data.get('avg_gas_price', 1)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if avg_gas_price > 0:
            gas_ratio = gas_price / avg_gas_price
            
            # Check for gas optimization opportunity
            if gas_ratio < self.gas_optimization_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'optimize_gas',
                        'confidence': self.calculate_confidence(gas_ratio),
                        'gas_ratio': gas_ratio,
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
        
    def calculate_confidence(self, gas_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gas ratio
        if gas_ratio < 0.15:
            confidence += 0.3
        elif gas_ratio < 0.3:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'gas_optimization_threshold': self.gas_optimization_threshold
        }
