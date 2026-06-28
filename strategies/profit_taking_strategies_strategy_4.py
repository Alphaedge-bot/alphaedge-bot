"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 4
Risk-based profit taking
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy4:
    """
    Profit Taking Strategies Strategy 4
    Bases profit taking on risk levels
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_4"
        self.name = "Profit Taking Strategies Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.risk_levels = {
            'low': {'min_gain': 0.10, 'scale': 0.20},
            'medium': {'min_gain': 0.15, 'scale': 0.30},
            'high': {'min_gain': 0.20, 'scale': 0.40}
        }
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        gain = data.get('gain', 0)
        risk_level = data.get('risk_level', 'medium')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if risk level is valid
        if risk_level in self.risk_levels:
            risk_config = self.risk_levels[risk_level]
            
            if gain >= risk_config['min_gain']:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'risk_based_take_profit',
                        'confidence': self.calculate_confidence(gain, risk_config),
                        'risk_level': risk_level,
                        'scale': risk_config['scale'],
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
        
    def calculate_confidence(self, gain: float, risk_config: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain vs min gain
        gain_ratio = gain / risk_config['min_gain'] if risk_config['min_gain'] > 0 else 0
        if gain_ratio > 1.3:
            confidence += 0.2
        elif gain_ratio > 1.1:
            confidence += 0.1
            
        # Scale
        if risk_config['scale'] > 0.3:
            confidence += 0.2
        elif risk_config['scale'] > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'risk_levels': self.risk_levels
        }
