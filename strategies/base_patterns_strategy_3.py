"""
AlphaEdge Strategy – Base Patterns Strategy 3
Triangle pattern breakout detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BasePatternsStrategy3:
    """
    Base Patterns Strategy 3
    Identifies triangle pattern breakouts
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "base_patterns_3"
        self.name = "Base Patterns Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.breakout_threshold = 0.015  # 1.5%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        pattern = data.get('pattern', 'none')
        price = data.get('price', 0)
        resistance = data.get('resistance', 0)
        support = data.get('support', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish triangle breakout
        if pattern in ['ascending_triangle', 'symmetrical_triangle']:
            if resistance > 0 and price > resistance * (1 + self.breakout_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(price, resistance, volume_ratio),
                        'pattern': 'bullish_breakout',
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for bearish triangle breakdown
        elif pattern in ['descending_triangle', 'symmetrical_triangle']:
            if support > 0 and price < support * (1 - self.breakout_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(price, support, volume_ratio),
                        'pattern': 'bearish_breakdown',
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
        
    def calculate_confidence(self, price: float, level: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout strength
        breakout_pct = abs(price - level) / level
        if breakout_pct > 0.025:
            confidence += 0.2
        elif breakout_pct > 0.015:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'breakout_threshold': self.breakout_threshold
        }
