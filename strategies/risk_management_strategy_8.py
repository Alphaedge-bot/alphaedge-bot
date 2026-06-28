"""
AlphaEdge Strategy – Risk Management Strategy 8
Stop-loss optimization and trailing stop management
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy8:
    """
    Risk Management Strategy 8
    Optimizes stop-loss and manages trailing stops
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_8"
        self.name = "Risk Management Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.stop_loss_threshold = 0.08  # 8%
        self.trailing_stop_percent = 0.05  # 5%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        price = data.get('price', 0)
        entry_price = data.get('entry_price', 0)
        highest_price = data.get('highest_price', entry_price)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_price > 0:
            current_loss = (entry_price - price) / entry_price
            
            # Check stop-loss trigger
            if current_loss > self.stop_loss_threshold:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'emergency_exit',
                    'confidence': self.calculate_confidence(current_loss, 'stop_loss'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
            # Check trailing stop
            if highest_price > entry_price:
                trailing_stop_price = highest_price * (1 - self.trailing_stop_percent)
                if price < trailing_stop_price:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'trailing_exit',
                        'confidence': self.calculate_confidence((highest_price - price) / highest_price, 'trailing'),
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
        
    def calculate_confidence(self, value: float, stop_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        if stop_type == 'stop_loss':
            if value > 0.12:
                confidence += 0.3
            elif value > 0.08:
                confidence += 0.15
                
        elif stop_type == 'trailing':
            if value > 0.08:
                confidence += 0.3
            elif value > 0.05:
                confidence += 0.15
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'stop_loss_threshold': self.stop_loss_threshold,
            'trailing_stop_percent': self.trailing_stop_percent
        }
