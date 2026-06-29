"""
AlphaEdge Strategy – Robustness & Resilience Strategy 10
Security breach detection and response
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RobustnessResilienceStrategy10:
    """
    Robustness & Resilience Strategy 10
    Detects security breaches and initiates response
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "robustness_resilience_10"
        self.name = "Robustness & Resilience Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.security_threat_threshold = 0.5
        self.breach_risk_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        security_threat = data.get('security_threat', 0)
        breach_risk = data.get('breach_risk', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for security breach signal
        if security_threat > self.security_threat_threshold:
            if breach_risk > self.breach_risk_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'security_response',
                        'confidence': self.calculate_confidence(security_threat, breach_risk),
                        'security_threat': security_threat,
                        'breach_risk': breach_risk,
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
        
    def calculate_confidence(self, security_threat: float, breach_risk: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Security threat
        if security_threat > 0.7:
            confidence += 0.2
        elif security_threat > 0.5:
            confidence += 0.1
            
        # Breach risk
        if breach_risk > 0.8:
            confidence += 0.2
        elif breach_risk > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'security_threat_threshold': self.security_threat_threshold,
            'breach_risk_threshold': self.breach_risk_threshold
        }
