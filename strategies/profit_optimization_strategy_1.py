"""
AlphaEdge Strategy – Profit Optimization Strategy 1
Dynamic take-profit optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy1:
    """
    Profit Optimization Strategy 1
    Optimizes take-profit levels dynamically
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_1"
        self.name = "Profit Optimization Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.tp_multipliers = [1.15, 1.25, 1.40, 1.50]
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
        volatility = data.get('volatility', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_price > 0:
            current_gain = (price - entry_price) / entry_price
            
            # Calculate dynamic take-profit levels
            tp_levels = []
            for multiplier in self.tp_multipliers:
                target_price = entry_price * multiplier
                target_gain = (target_price - entry_price) / entry_price
                
                # Adjust for volatility
                volatility_adjustment = 1 + (volatility * 0.5)
                adjusted_target = target_price * volatility_adjustment
                
                tp_levels.append({
                    'price': adjusted_target,
                    'gain': target_gain * 100,
                    'multiplier': multiplier
                })
                
            # Check if any TP level is reached
            for level in tp_levels:
                if price >= level['price']:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'take_profit',
                            'confidence': self.calculate_confidence(current_gain, level['gain']),
                            'tp_level': level,
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
        
    def calculate_confidence(self, current_gain: float, target_gain: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain ratio
        gain_ratio = current_gain / target_gain if target_gain > 0 else 0
        if gain_ratio > 0.9:
            confidence += 0.2
        elif gain_ratio > 0.7:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tp_multipliers': self.tp_multipliers
        }
