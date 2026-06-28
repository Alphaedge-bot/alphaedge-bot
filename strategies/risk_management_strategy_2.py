"""
AlphaEdge Strategy – Risk Management Strategy 2
Maximum drawdown and loss limit controls
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy2:
    """
    Risk Management Strategy 2
    Controls maximum drawdown and loss limits
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_2"
        self.name = "Risk Management Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.max_drawdown = 0.10  # 10%
        self.daily_loss_limit = 0.03  # 3%
        self.weekly_loss_limit = 0.05  # 5%
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_drawdown = data.get('drawdown', 0)
        daily_loss = data.get('daily_loss', 0)
        weekly_loss = data.get('weekly_loss', 0)
        
        # Check if any limits are breached
        if current_drawdown > self.max_drawdown:
            signal = {
                'strategy': self.strategy_id,
                'type': 'emergency_exit',
                'confidence': self.calculate_confidence(current_drawdown, 'drawdown'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        elif daily_loss > self.daily_loss_limit:
            signal = {
                'strategy': self.strategy_id,
                'type': 'pause_trading',
                'confidence': self.calculate_confidence(daily_loss, 'daily'),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        elif weekly_loss > self.weekly_loss_limit:
            signal = {
                'strategy': self.strategy_id,
                'type': 'reduce_position',
                'confidence': self.calculate_confidence(weekly_loss, 'weekly'),
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
        
    def calculate_confidence(self, value: float, limit_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        if limit_type == 'drawdown':
            if value > 0.15:
                confidence += 0.4
            elif value > 0.1:
                confidence += 0.2
                
        elif limit_type == 'daily':
            if value > 0.05:
                confidence += 0.4
            elif value > 0.03:
                confidence += 0.2
                
        elif limit_type == 'weekly':
            if value > 0.08:
                confidence += 0.4
            elif value > 0.05:
                confidence += 0.2
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'max_drawdown': self.max_drawdown,
            'daily_loss_limit': self.daily_loss_limit,
            'weekly_loss_limit': self.weekly_loss_limit
        }
