"""
AlphaEdge Strategy – Risk Management Strategy 4
Value at Risk (VaR) and Expected Shortfall (ES) monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy4:
    """
    Risk Management Strategy 4
    Monitors VaR and Expected Shortfall
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_4"
        self.name = "Risk Management Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.var_95_limit = 0.02  # 2%
        self.var_99_limit = 0.04  # 4%
        self.es_limit = 0.03  # 3%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        var_95 = data.get('var_95', 0)
        var_99 = data.get('var_99', 0)
        es = data.get('es', 0)
        
        # Check VaR limits
        if var_95 > self.var_95_limit:
            signal = {
                'strategy': self.strategy_id,
                'type': 'reduce_risk',
                'confidence': self.calculate_confidence(var_95, 'var_95'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        if var_99 > self.var_99_limit:
            signal = {
                'strategy': self.strategy_id,
                'type': 'hedge_position',
                'confidence': self.calculate_confidence(var_99, 'var_99'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        if es > self.es_limit:
            signal = {
                'strategy': self.strategy_id,
                'type': 'risk_emergency',
                'confidence': self.calculate_confidence(es, 'es'),
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
        
    def calculate_confidence(self, value: float, risk_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        if risk_type == 'var_95':
            if value > 0.04:
                confidence += 0.3
            elif value > 0.02:
                confidence += 0.15
                
        elif risk_type == 'var_99':
            if value > 0.06:
                confidence += 0.3
            elif value > 0.04:
                confidence += 0.15
                
        elif risk_type == 'es':
            if value > 0.05:
                confidence += 0.3
            elif value > 0.03:
                confidence += 0.15
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'var_95_limit': self.var_95_limit,
            'var_99_limit': self.var_99_limit,
            'es_limit': self.es_limit
        }
