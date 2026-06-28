"""
AlphaEdge Strategy – Risk Management Strategy 10
Stress testing and scenario analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy10:
    """
    Risk Management Strategy 10
    Performs stress testing and scenario analysis
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_10"
        self.name = "Risk Management Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.stress_threshold = 0.15  # 15%
        self.scenario_count = 100
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        stress_score = data.get('stress_score', 0)
        worst_case = data.get('worst_case', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high stress scenario
        if stress_score > self.stress_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'stress_reduce',
                    'confidence': self.calculate_confidence(stress_score, worst_case),
                    'worst_case': worst_case,
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
        
    def calculate_confidence(self, stress_score: float, worst_case: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Stress score
        if stress_score > 0.3:
            confidence += 0.2
        elif stress_score > 0.15:
            confidence += 0.1
            
        # Worst case impact
        if worst_case > 0.3:
            confidence += 0.2
        elif worst_case > 0.15:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'stress_threshold': self.stress_threshold,
            'scenario_count': self.scenario_count
        }
