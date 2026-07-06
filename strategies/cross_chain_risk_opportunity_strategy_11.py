"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 11
Cross-chain bridge gas cost analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy11:
    """
    Cross-Chain Risk & Opportunity Strategy 11
    Analyzes cross-chain bridge gas costs
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_11"
        self.name = "Cross-Chain Risk & Opportunity Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.gas_cost_threshold = 10  # USD
        self.cost_efficiency_threshold = 0.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_gas_cost = data.get('bridge_gas_cost', 0)
        cost_efficiency = data.get('cost_efficiency', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge gas cost signal
        if bridge_gas_cost < self.gas_cost_threshold:
            if cost_efficiency > self.cost_efficiency_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_cost_efficient',
                        'confidence': self.calculate_confidence(bridge_gas_cost, cost_efficiency),
                        'bridge_gas_cost': bridge_gas_cost,
                        'cost_efficiency': cost_efficiency,
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
        
    def calculate_confidence(self, bridge_gas_cost: float, cost_efficiency: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Bridge gas cost
        if bridge_gas_cost < 5:
            confidence += 0.2
        elif bridge_gas_cost < 10:
            confidence += 0.1
            
        # Cost efficiency
        if cost_efficiency > 0.7:
            confidence += 0.2
        elif cost_efficiency > 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'gas_cost_threshold': self.gas_cost_threshold,
            'cost_efficiency_threshold': self.cost_efficiency_threshold
        }
