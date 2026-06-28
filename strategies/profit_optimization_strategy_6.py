"""
AlphaEdge Strategy – Profit Optimization Strategy 6
Risk-reward ratio optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy6:
    """
    Profit Optimization Strategy 6
    Optimizes risk-reward ratios
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_6"
        self.name = "Profit Optimization Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.target_rr = 2.0
        self.max_rr = 3.0
        self.min_rr = 1.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_rr = data.get('risk_reward_ratio', 0)
        position_size = data.get('position_size', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if RR optimization is needed
        if current_rr > 0 and current_rr < self.target_rr:
            if volume_ratio > self.volume_confirm:
                # Calculate optimal position adjustment
                rr_ratio = self.target_rr / current_rr if current_rr > 0 else 1
                adjusted_size = position_size * rr_ratio
                
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'adjust_position',
                    'confidence': self.calculate_confidence(current_rr, self.target_rr),
                    'adjusted_size': adjusted_size,
                    'current_rr': current_rr,
                    'target_rr': self.target_rr,
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
        
    def calculate_confidence(self, current_rr: float, target_rr: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # RR gap
        rr_gap = target_rr - current_rr
        if rr_gap > 0.5:
            confidence += 0.2
        elif rr_gap > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'target_rr': self.target_rr,
            'max_rr': self.max_rr,
            'min_rr': self.min_rr
        }
