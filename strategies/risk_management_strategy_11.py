"""
AlphaEdge Strategy – Risk Management Strategy 11
Risk-adjusted return optimization (Sharpe ratio focus)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy11:
    """
    Risk Management Strategy 11
    Optimizes for risk-adjusted returns (Sharpe ratio)
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_11"
        self.name = "Risk Management Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.sharpe_threshold = 1.5
        self.sharpe_target = 2.0
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_sharpe = data.get('sharpe_ratio', 0)
        expected_return = data.get('expected_return', 0)
        volatility = data.get('volatility', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate if Sharpe ratio is improving
        if current_sharpe > self.sharpe_threshold:
            if volume_ratio > self.volume_confirm:
                # Calculate optimal position adjustment
                sharpe_ratio = expected_return / volatility if volatility > 0 else 0
                
                if sharpe_ratio > self.sharpe_target:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'increase_position',
                        'confidence': self.calculate_confidence(sharpe_ratio, expected_return),
                        'sharpe_ratio': sharpe_ratio,
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
        
    def calculate_confidence(self, sharpe_ratio: float, expected_return: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sharpe ratio
        if sharpe_ratio > 2.5:
            confidence += 0.3
        elif sharpe_ratio > 2.0:
            confidence += 0.15
            
        # Expected return
        if expected_return > 0.3:
            confidence += 0.2
        elif expected_return > 0.15:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'sharpe_threshold': self.sharpe_threshold,
            'sharpe_target': self.sharpe_target
        }
