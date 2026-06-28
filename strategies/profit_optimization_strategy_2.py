"""
AlphaEdge Strategy – Profit Optimization Strategy 2
Pyramiding position optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy2:
    """
    Profit Optimization Strategy 2
    Optimizes pyramiding positions
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_2"
        self.name = "Profit Optimization Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.pyramid_increments = [0.20, 0.50, 1.00, 2.00]
        self.max_pyramid_positions = 4
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
        current_size = data.get('position_size', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_price > 0:
            gain = (price - entry_price) / entry_price
            
            # Check pyramiding opportunities
            for i, increment in enumerate(self.pyramid_increments):
                if i >= self.max_pyramid_positions:
                    break
                    
                target_gain = increment
                if gain >= target_gain:
                    # Calculate additional position size
                    additional_size = current_size * (increment / 2)
                    
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'pyramid',
                            'confidence': self.calculate_confidence(gain, target_gain),
                            'additional_size': additional_size,
                            'increment': increment,
                            'level': i + 1,
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
        
    def calculate_confidence(self, gain: float, target_gain: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain ratio
        gain_ratio = gain / target_gain if target_gain > 0 else 0
        if gain_ratio > 1.2:
            confidence += 0.2
        elif gain_ratio > 1.0:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pyramid_increments': self.pyramid_increments,
            'max_pyramid_positions': self.max_pyramid_positions
        }
