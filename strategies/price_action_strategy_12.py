"""
AlphaEdge Strategy – Price Action Strategy 12
Advanced pattern combination (multi-pattern recognition)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PriceActionStrategy12:
    """
    Price Action Strategy 12
    Uses advanced pattern combination for high-confidence signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "price_action_12"
        self.name = "Price Action Strategy 12"
        self.active = True
        
        # Strategy parameters
        self.pattern_weight = {
            'engulfing': 0.25,
            'pin_bar': 0.25,
            'inside_bar': 0.20,
            'breakout': 0.30
        }
        self.confidence_threshold = 0.6
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        patterns = data.get('patterns', {})
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate pattern score
        score = 0
        pattern_count = 0
        
        for pattern, weight in self.pattern_weight.items():
            if patterns.get(pattern, False):
                score += weight
                pattern_count += 1
                
        # Volume confirmation
        if volume_ratio > 1.2:
            score += 0.1
            
        # Check if enough patterns are present
        if pattern_count >= 2 and score > self.confidence_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(score, pattern_count),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for sell signals (bearish patterns)
        bearish_patterns = ['bearish_engulfing', 'shooting_star', 'evening_star']
        bearish_count = sum(1 for p in bearish_patterns if patterns.get(p, False))
        
        if bearish_count >= 2:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': 0.6 + (bearish_count * 0.1),
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
        
    def calculate_confidence(self, score: float, pattern_count: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Score contribution
        if score > 0.8:
            confidence += 0.3
        elif score > 0.6:
            confidence += 0.15
            
        # Pattern count contribution
        if pattern_count >= 3:
            confidence += 0.2
        elif pattern_count >= 2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pattern_weight': self.pattern_weight
        }
