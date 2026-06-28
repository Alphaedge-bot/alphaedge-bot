"""
AlphaEdge Strategy – Profit Optimization Strategy 7
Profit factor maximization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizationStrategy7:
    """
    Profit Optimization Strategy 7
    Maximizes profit factor
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_optimization_7"
        self.name = "Profit Optimization Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.target_profit_factor = 2.0
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_pf = data.get('profit_factor', 0)
        win_rate = data.get('win_rate', 0.5)
        avg_win = data.get('avg_win', 0)
        avg_loss = data.get('avg_loss', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if profit factor can be improved
        if current_pf > 0 and current_pf < self.target_profit_factor:
            if avg_loss > 0:
                # Calculate optimal risk-reward
                optimal_rr = self.target_profit_factor / win_rate if win_rate > 0 else 0
                
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'optimize_rr',
                        'confidence': self.calculate_confidence(current_pf, self.target_profit_factor),
                        'optimal_rr': optimal_rr,
                        'current_pf': current_pf,
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
        
    def calculate_confidence(self, current_pf: float, target_pf: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # PF gap
        pf_gap = target_pf - current_pf
        if pf_gap > 0.5:
            confidence += 0.2
        elif pf_gap > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'target_profit_factor': self.target_profit_factor
        }
