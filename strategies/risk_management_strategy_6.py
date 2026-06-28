"""
AlphaEdge Strategy – Risk Management Strategy 6
Leverage management and margin monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy6:
    """
    Risk Management Strategy 6
    Manages leverage and monitors margin
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_6"
        self.name = "Risk Management Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.max_leverage = 3.0
        self.min_margin_ratio = 0.2  # 20%
        self.liquidation_threshold = 0.3  # 30%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_leverage = data.get('leverage', 0)
        margin_ratio = data.get('margin_ratio', 0)
        liquidation_risk = data.get('liquidation_risk', 0)
        
        # Check leverage limit
        if current_leverage > self.max_leverage:
            signal = {
                'strategy': self.strategy_id,
                'type': 'reduce_leverage',
                'confidence': self.calculate_confidence(current_leverage, 'leverage'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check margin ratio
        if margin_ratio < self.min_margin_ratio:
            signal = {
                'strategy': self.strategy_id,
                'type': 'add_margin',
                'confidence': self.calculate_confidence(margin_ratio, 'margin'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check liquidation risk
        if liquidation_risk > self.liquidation_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'emergency_reduce',
                'confidence': self.calculate_confidence(liquidation_risk, 'liquidation'),
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
        
        if risk_type == 'leverage':
            if value > 5.0:
                confidence += 0.3
            elif value > 3.0:
                confidence += 0.15
                
        elif risk_type == 'margin':
            if value < 0.1:
                confidence += 0.3
            elif value < 0.2:
                confidence += 0.15
                
        elif risk_type == 'liquidation':
            if value > 0.5:
                confidence += 0.3
            elif value > 0.3:
                confidence += 0.15
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'max_leverage': self.max_leverage,
            'min_margin_ratio': self.min_margin_ratio,
            'liquidation_threshold': self.liquidation_threshold
        }
