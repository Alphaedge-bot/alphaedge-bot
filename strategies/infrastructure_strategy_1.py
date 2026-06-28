"""
AlphaEdge Strategy – Infrastructure Strategy 1
Network upgrade and protocol improvement monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class InfrastructureStrategy1:
    """
    Infrastructure Strategy 1
    Monitors network upgrades and protocol improvements
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "infrastructure_1"
        self.name = "Infrastructure Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.upgrade_impact_threshold = 0.3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("infrastructure_data_update", self.handle_infrastructure_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_infrastructure_data(self, event: Event):
        """Handle infrastructure data updates"""
        data = event.data
        network_upgrades = data.get('network_upgrades', [])
        protocol_improvements = data.get('protocol_improvements', [])
        upgrade_impact = data.get('upgrade_impact', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for significant upgrades
        if network_upgrades or protocol_improvements:
            if upgrade_impact > self.upgrade_impact_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(upgrade_impact, network_upgrades, protocol_improvements),
                        'upgrade_count': len(network_upgrades) + len(protocol_improvements),
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
        
    def calculate_confidence(self, upgrade_impact: float, network_upgrades: list, protocol_improvements: list) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Upgrade impact
        if upgrade_impact > 0.5:
            confidence += 0.2
        elif upgrade_impact > 0.3:
            confidence += 0.1
            
        # Number of upgrades
        total_upgrades = len(network_upgrades) + len(protocol_improvements)
        if total_upgrades > 3:
            confidence += 0.2
        elif total_upgrades > 0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'upgrade_impact_threshold': self.upgrade_impact_threshold
        }
