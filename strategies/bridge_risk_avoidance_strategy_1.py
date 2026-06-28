"""
AlphaEdge Strategy – Bridge Risk Avoidance Strategy 1
Bridge vulnerability and attack detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BridgeRiskAvoidanceStrategy1:
    """
    Bridge Risk Avoidance Strategy 1
    Detects bridge vulnerabilities and attacks
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bridge_risk_avoidance_1"
        self.name = "Bridge Risk Avoidance Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.bridge_risk_threshold = 0.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("bridge_data_update", self.handle_bridge_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_bridge_data(self, event: Event):
        """Handle bridge data updates"""
        data = event.data
        bridge_risk_score = data.get('bridge_risk_score', 0)
        bridge_attacks = data.get('bridge_attacks', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high bridge risk
        if bridge_risk_score > self.bridge_risk_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'avoid_bridge',
                    'confidence': self.calculate_confidence(bridge_risk_score, bridge_attacks),
                    'bridge_risk_score': bridge_risk_score,
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
        
    def calculate_confidence(self, risk_score: float, attacks: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Risk score
        if risk_score > 0.7:
            confidence += 0.2
        elif risk_score > 0.5:
            confidence += 0.1
            
        # Attack count
        if attacks > 0:
            confidence += 0.2
        elif attacks > 0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'bridge_risk_threshold': self.bridge_risk_threshold
        }
