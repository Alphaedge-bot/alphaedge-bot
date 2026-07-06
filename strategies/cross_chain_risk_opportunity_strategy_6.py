"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 6
Cross-chain bridge volume and velocity analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy6:
    """
    Cross-Chain Risk & Opportunity Strategy 6
    Analyzes cross-chain bridge volume and velocity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_6"
        self.name = "Cross-Chain Risk & Opportunity Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.volume_growth_threshold = 0.3  # 30%
        self.velocity_threshold = 0.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_volume_growth = data.get('bridge_volume_growth', 0)
        bridge_velocity = data.get('bridge_velocity', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge volume signal
        if bridge_volume_growth > self.volume_growth_threshold:
            if bridge_velocity > self.velocity_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_volume_surge',
                        'confidence': self.calculate_confidence(bridge_volume_growth, bridge_velocity),
                        'bridge_volume_growth': bridge_volume_growth,
                        'bridge_velocity': bridge_velocity,
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
        
    def calculate_confidence(self, volume_growth: float, velocity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Volume growth
        if volume_growth > 0.5:
            confidence += 0.2
        elif volume_growth > 0.3:
            confidence += 0.1
            
        # Velocity
        if velocity > 0.7:
            confidence += 0.2
        elif velocity > 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'volume_growth_threshold': self.volume_growth_threshold,
            'velocity_threshold': self.velocity_threshold
        }
