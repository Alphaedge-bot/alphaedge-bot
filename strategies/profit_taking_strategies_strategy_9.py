"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 9
Profit taking with momentum confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy9:
    """
    Profit Taking Strategies Strategy 9
    Confirms profit taking with momentum indicators
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_9"
        self.name = "Profit Taking Strategies Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.momentum_threshold = 0.5
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
        momentum = data.get('momentum', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if momentum is weakening
        if gain > 0.1:  # At least 10% gain
            if momentum < self.momentum_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'momentum_take_profit',
                        'confidence': self.calculate_confidence(gain, momentum),
                        'momentum': momentum,
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
        
    def calculate_confidence(self, gain: float, momentum: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain
        if gain > 0.2:
            confidence += 0.2
        elif gain > 0.15:
            confidence += 0.1
            
        # Momentum
        if momentum < 0.3:
            confidence += 0.2
        elif momentum < 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'momentum_threshold': self.momentum_threshold
        }
