"""
AlphaEdge Strategy – Robustness & Resilience Strategy 11
Disaster recovery and business continuity
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RobustnessResilienceStrategy11:
    """
    Robustness & Resilience Strategy 11
    Manages disaster recovery and business continuity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "robustness_resilience_11"
        self.name = "Robustness & Resilience Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.disaster_recovery_threshold = 0.7
        self.business_continuity_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        disaster_recovery = data.get('disaster_recovery', 0)
        business_continuity = data.get('business_continuity', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for disaster recovery signal
        if disaster_recovery > self.disaster_recovery_threshold:
            if business_continuity > self.business_continuity_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'disaster_recovery',
                        'confidence': self.calculate_confidence(disaster_recovery, business_continuity),
                        'disaster_recovery': disaster_recovery,
                        'business_continuity': business_continuity,
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
        
    def calculate_confidence(self, disaster_recovery: float, business_continuity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Disaster recovery
        if disaster_recovery > 0.85:
            confidence += 0.2
        elif disaster_recovery > 0.7:
            confidence += 0.1
            
        # Business continuity
        if business_continuity > 0.8:
            confidence += 0.2
        elif business_continuity > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'disaster_recovery_threshold': self.disaster_recovery_threshold,
            'business_continuity_threshold': self.business_continuity_threshold
        }
