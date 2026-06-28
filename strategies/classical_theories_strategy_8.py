"""
AlphaEdge Strategy – Classical Theories Strategy 8
Breakout and continuation pattern recognition
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ClassicalTheoriesStrategy8:
    """
    Classical Theories Strategy 8
    Recognizes breakout and continuation patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "classical_theories_8"
        self.name = "Classical Theories Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.pattern_threshold = 0.02  # 2%
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
        pattern = data.get('pattern', 'none')
        breakout_level = data.get('breakout_level', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bullish breakout
        if pattern == 'bullish_breakout':
            if breakout_level > 0 and price > breakout_level * (1 + self.pattern_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(pattern, price, breakout_level),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for bearish breakdown
        elif pattern == 'bearish_breakdown':
            if breakout_level > 0 and price < breakout_level * (1 - self.pattern_threshold):
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(pattern, price, breakout_level),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for continuation pattern
        elif pattern in ['bull_flag', 'bear_flag', 'pennant']:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy' if pattern == 'bull_flag' else 'sell',
                    'confidence': 0.6,
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
        
    def calculate_confidence(self, pattern: str, price: float, breakout_level: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern strength
        if pattern in ['bullish_breakout', 'bearish_breakdown']:
            confidence += 0.2
            
        # Breakout strength
        if breakout_level > 0:
            breakout_pct = abs(price - breakout_level) / breakout_level
            if breakout_pct > 0.03:
                confidence += 0.2
            elif breakout_pct > 0.02:
                confidence += 0.1
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pattern_threshold': self.pattern_threshold
        }
