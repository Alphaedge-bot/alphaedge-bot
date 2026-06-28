"""
AlphaEdge Strategy – Risk Management Strategy 1
Position sizing based on Kelly Criterion
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy1:
    """
    Risk Management Strategy 1
    Uses Kelly Criterion for optimal position sizing
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_1"
        self.name = "Risk Management Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.kelly_fraction = 0.25
        self.max_position = 0.06  # 6%
        self.min_position = 0.01  # 1%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        win_rate = data.get('win_rate', 0.5)
        avg_win = data.get('avg_win', 0)
        avg_loss = data.get('avg_loss', 0)
        
        if avg_loss > 0:
            # Calculate Kelly fraction
            edge = (avg_win - avg_loss) / avg_loss
            kelly = win_rate - (1 - win_rate) / edge if edge > 0 else 0
            
            # Apply Kelly fraction
            kelly_position = kelly * self.kelly_fraction
            
            # Clamp to min/max
            position_size = max(self.min_position, min(self.max_position, kelly_position))
            
            # If position size is meaningful, generate signal
            if position_size > self.min_position:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'position_sizing',
                    'confidence': self.calculate_confidence(kelly, position_size),
                    'position_size': position_size,
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
        
    def calculate_confidence(self, kelly: float, position_size: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Kelly value
        if kelly > 0.3:
            confidence += 0.2
        elif kelly > 0.1:
            confidence += 0.1
            
        # Position size
        if position_size > 0.04:
            confidence += 0.2
        elif position_size > 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'kelly_fraction': self.kelly_fraction,
            'max_position': self.max_position,
            'min_position': self.min_position
        }
