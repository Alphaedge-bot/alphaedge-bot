"""
AlphaEdge Strategy – Risk Management Strategy 3
Correlation risk and portfolio diversification
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy3:
    """
    Risk Management Strategy 3
    Manages correlation risk and portfolio diversification
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_3"
        self.name = "Risk Management Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.correlation_threshold = 0.7
        self.max_sector_exposure = 0.3  # 30%
        self.diversification_target = 0.5  # 50%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        correlation_matrix = data.get('correlation_matrix', {})
        sector_exposure = data.get('sector_exposure', 0)
        diversification_score = data.get('diversification_score', 0)
        
        # Check for high correlation risk
        max_correlation = 0
        for assets, corr in correlation_matrix.items():
            if isinstance(corr, (int, float)):
                max_correlation = max(max_correlation, abs(corr))
                
        if max_correlation > self.correlation_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'reduce_correlation',
                'confidence': self.calculate_confidence(max_correlation, 'correlation'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for over-concentration
        if sector_exposure > self.max_sector_exposure:
            signal = {
                'strategy': self.strategy_id,
                'type': 'rebalance_sector',
                'confidence': self.calculate_confidence(sector_exposure, 'sector'),
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
        
        if risk_type == 'correlation':
            if value > 0.85:
                confidence += 0.3
            elif value > 0.7:
                confidence += 0.15
                
        elif risk_type == 'sector':
            if value > 0.4:
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
            'correlation_threshold': self.correlation_threshold,
            'max_sector_exposure': self.max_sector_exposure
        }
