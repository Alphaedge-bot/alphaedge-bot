"""
AlphaEdge Strategy – Bridge Risk Avoidance Strategy 2
Cross-chain bridge risk analysis and avoidance
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BridgeRiskAvoidanceStrategy2:
    """
    Bridge Risk Avoidance Strategy 2
    Analyzes cross-chain bridge risks and provides avoidance
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bridge_risk_avoidance_2"
        self.name = "Bridge Risk Avoidance Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.cross_chain_risk_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("bridge_data_update", self.handle_bridge_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_bridge_data(self, event: Event):
        """Handle bridge data updates"""
        data = event.data
        cross_chain_risk = data.get('cross_chain_risk', 0)
        bridge_volume = data.get('bridge_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for cross-chain risk
        if cross_chain_risk > self.cross_chain_risk_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'avoid_cross_chain',
                    'confidence': self.calculate_confidence(cross_chain_risk, bridge_volume),
                    'cross_chain_risk': cross_chain_risk,
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
        
    def calculate_confidence(self, risk: float, volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Cross-chain risk
        if risk > 0.8:
            confidence += 0.2
        elif risk > 0.6:
            confidence += 0.1
            
        # Bridge volume
        if volume > 1000000:
            confidence += 0.2
        elif volume > 100000:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'cross_chain_risk_threshold': self.cross_chain_risk_threshold
        }
