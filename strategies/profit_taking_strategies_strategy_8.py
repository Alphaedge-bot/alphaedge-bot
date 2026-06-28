"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 8
Algorithmic profit taking (rule-based)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy8:
    """
    Profit Taking Strategies Strategy 8
    Uses algorithmic rule-based profit taking
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_8"
        self.name = "Profit Taking Strategies Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.rules = [
            {'condition': 'gain > 0.15', 'action': 'take_25%'},
            {'condition': 'gain > 0.25', 'action': 'take_50%'},
            {'condition': 'gain > 0.35', 'action': 'take_75%'},
            {'condition': 'gain > 0.50', 'action': 'take_100%'}
        ]
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
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check each rule
        for rule in self.rules:
            condition = rule['condition']
            action = rule['action']
            
            # Evaluate condition
            if eval(condition):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'algorithmic_take_profit',
                        'confidence': self.calculate_confidence(gain, action),
                        'action': action,
                        'gain': gain,
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    break  # Only take one action per bar
                    
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
        
    def calculate_confidence(self, gain: float, action: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gain
        if gain > 0.3:
            confidence += 0.2
        elif gain > 0.2:
            confidence += 0.1
            
        # Action
        if '100%' in action:
            confidence += 0.2
        elif '75%' in action:
            confidence += 0.15
        elif '50%' in action:
            confidence += 0.1
        elif '25%' in action:
            confidence += 0.05
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'rules': self.rules
        }
