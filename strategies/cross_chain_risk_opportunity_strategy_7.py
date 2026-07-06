"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 7
Cross-chain bridge TVL analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy7:
    """
    Cross-Chain Risk & Opportunity Strategy 7
    Analyzes cross-chain bridge TVL
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_7"
        self.name = "Cross-Chain Risk & Opportunity Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.tvl_threshold = 100000000  # $100M
        self.tvl_growth_threshold = 0.1  # 10%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_tvl = data.get('bridge_tvl', 0)
        tvl_growth = data.get('tvl_growth', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge TVL signal
        if bridge_tvl > self.tvl_threshold:
            if tvl_growth > self.tvl_growth_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_tvl_growth',
                        'confidence': self.calculate_confidence(bridge_tvl, tvl_growth),
                        'bridge_tvl': bridge_tvl,
                        'tvl_growth': tvl_growth,
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
        
    def calculate_confidence(self, bridge_tvl: float, tvl_growth: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Bridge TVL
        if bridge_tvl > 500000000:
            confidence += 0.2
        elif bridge_tvl > 100000000:
            confidence += 0.1
            
        # TVL growth
        if tvl_growth > 0.2:
            confidence += 0.2
        elif tvl_growth > 0.1:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tvl_threshold': self.tvl_threshold,
            'tvl_growth_threshold': self.tvl_growth_threshold
        }
