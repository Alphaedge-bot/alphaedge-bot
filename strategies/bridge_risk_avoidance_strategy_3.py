"""
AlphaEdge Strategy – Bridge Risk Avoidance Strategy 3
Bridge risk composite and avoidance decision
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BridgeRiskAvoidanceStrategy3:
    """
    Bridge Risk Avoidance Strategy 3
    Comprehensive bridge risk composite and avoidance decision
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bridge_risk_avoidance_3"
        self.name = "Bridge Risk Avoidance Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.composite_threshold = 0.6
        self.weights = {
            'vulnerability': 0.30,
            'attack_history': 0.25,
            'liquidity': 0.20,
            'usage': 0.15,
            'reputation': 0.10
        }
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("bridge_data_update", self.handle_bridge_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_bridge_data(self, event: Event):
        """Handle bridge data updates"""
        data = event.data
        
        # Calculate composite risk
        composite = 0
        for key, weight in self.weights.items():
            value = data.get(key, 0.5)
            composite += value * weight
            
        # Check for high composite risk
        if composite > self.composite_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'avoid_all_bridges',
                'confidence': self.calculate_confidence(composite, data),
                'composite_score': composite,
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
        
    def calculate_confidence(self, composite: float, data: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Composite strength
        if composite > 0.8:
            confidence += 0.3
        elif composite > 0.6:
            confidence += 0.15
            
        # Component alignment
        components = [data.get(k, 0.5) for k in self.weights.keys()]
        high_risk = sum(1 for c in components if c > 0.7)
        if high_risk >= 3:
            confidence += 0.2
        elif high_risk >= 2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'weights': self.weights,
            'composite_threshold': self.composite_threshold
        }
