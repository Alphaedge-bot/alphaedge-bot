"""
AlphaEdge Strategy – Market Sentiment Strategy 4
Crypto Fear and Greed Index momentum analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketSentimentStrategy4:
    """
    Market Sentiment Strategy 4
    Analyzes Fear & Greed Index momentum
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "market_sentiment_4"
        self.name = "Market Sentiment Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.momentum_threshold = 5.0  # points change
        self.sentiment_threshold = 50
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        fear_greed = data.get('fear_greed', 50)
        prev_fear_greed = data.get('prev_fear_greed', 50)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate momentum
        momentum = fear_greed - prev_fear_greed
        
        # Check for bullish momentum
        if momentum > self.momentum_threshold and fear_greed < self.sentiment_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(momentum, fear_greed),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for bearish momentum
        elif momentum < -self.momentum_threshold and fear_greed > self.sentiment_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(momentum, fear_greed),
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
        
    def calculate_confidence(self, momentum: float, fear_greed: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Momentum strength
        if abs(momentum) > 10:
            confidence += 0.3
        elif abs(momentum) > 5:
            confidence += 0.15
            
        # Sentiment extreme
        if fear_greed < 30 or fear_greed > 70:
            confidence += 0.2
        elif fear_greed < 40 or fear_greed > 60:
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
