"""
AlphaEdge Strategy – Risk Management Strategy 7
Tail risk hedging and black swan protection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy7:
    """
    Risk Management Strategy 7
    Provides tail risk hedging and black swan protection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_7"
        self.name = "Risk Management Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.tail_risk_threshold = 0.1  # 10%
        self.hedge_ratio = 0.05  # 5%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        tail_risk = data.get('tail_risk', 0)
        volatility = data.get('volatility', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high tail risk
        if tail_risk > self.tail_risk_threshold:
            if volume_ratio > self.volume_confirm:
                # Calculate hedge amount
                hedge_amount = self.hedge_ratio * (tail_risk / self.tail_risk_threshold)
                
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'hedge_position',
                    'confidence': self.calculate_confidence(tail_risk, hedge_amount),
                    'hedge_amount': hedge_amount,
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
        
    def calculate_confidence(self, tail_risk: float, hedge_amount: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Tail risk
        if tail_risk > 0.2:
            confidence += 0.2
        elif tail_risk > 0.1:
            confidence += 0.1
            
        # Hedge amount
        if hedge_amount > 0.1:
            confidence += 0.2
        elif hedge_amount > 0.05:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tail_risk_threshold': self.tail_risk_threshold,
            'hedge_ratio': self.hedge_ratio
        }
