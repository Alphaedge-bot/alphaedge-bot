"""
AlphaEdge Strategy – Operational Strategies Strategy 2
Risk monitoring and position management
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OperationalStrategiesStrategy2:
    """
    Operational Strategies Strategy 2
    Monitors risk and manages positions
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "operational_strategies_2"
        self.name = "Operational Strategies Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.risk_monitoring_threshold = 0.5
        self.position_management_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        risk_score = data.get('risk_score', 0)
        position_health = data.get('position_health', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for risk monitoring opportunity
        if risk_score > self.risk_monitoring_threshold:
            if position_health > self.position_management_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'manage_positions',
                        'confidence': self.calculate_confidence(risk_score, position_health),
                        'risk_score': risk_score,
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
        
    def calculate_confidence(self, risk_score: float, position_health: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Risk score
        if risk_score > 0.7:
            confidence += 0.2
        elif risk_score > 0.5:
            confidence += 0.1
            
        # Position health
        if position_health > 0.8:
            confidence += 0.2
        elif position_health > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'risk_monitoring_threshold': self.risk_monitoring_threshold,
            'position_management_threshold': self.position_management_threshold
        }
