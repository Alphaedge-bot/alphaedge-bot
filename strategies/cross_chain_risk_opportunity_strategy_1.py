"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 1
Bridge risk assessment and monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy1:
    """
    Cross-Chain Risk & Opportunity Strategy 1
    Assesses and monitors bridge risks
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_1"
        self.name = "Cross-Chain Risk & Opportunity Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.bridge_risk_threshold = 0.6
        self.bridge_volume_threshold = 1000000  # $1M
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_risk = data.get('bridge_risk', 0)
        bridge_volume = data.get('bridge_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge risk signal
        if bridge_risk > self.bridge_risk_threshold:
            if bridge_volume > self.bridge_volume_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_risk_detected',
                        'confidence': self.calculate_confidence(bridge_risk, bridge_volume),
                        'bridge_risk': bridge_risk,
                        'bridge_volume': bridge_volume,
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
        
    def calculate_confidence(self, bridge_risk: float, bridge_volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Bridge risk
        if bridge_risk > 0.8:
            confidence += 0.2
        elif bridge_risk > 0.6:
            confidence += 0.1
            
        # Bridge volume
        if bridge_volume > 5000000:
            confidence += 0.2
        elif bridge_volume > 1000000:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'bridge_risk_threshold': self.bridge_risk_threshold,
            'bridge_volume_threshold': self.bridge_volume_threshold
        }
