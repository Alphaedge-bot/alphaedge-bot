"""
AlphaEdge Strategy – Market Sentiment Strategy 9
Sentiment volume and velocity analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketSentimentStrategy9:
    """
    Market Sentiment Strategy 9
    Analyzes sentiment volume and velocity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "market_sentiment_9"
        self.name = "Market Sentiment Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.sentiment_volume_threshold = 1000
        self.velocity_threshold = 0.1  # 10% change
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        sentiment_volume = data.get('sentiment_volume', 0)
        sentiment_velocity = data.get('sentiment_velocity', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high sentiment volume with velocity (buy)
        if sentiment_volume > self.sentiment_volume_threshold:
            if sentiment_velocity > self.velocity_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(sentiment_volume, sentiment_velocity),
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
        
    def calculate_confidence(self, volume: float, velocity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sentiment volume
        if volume > 5000:
            confidence += 0.2
        elif volume > 1000:
            confidence += 0.1
            
        # Velocity
        if velocity > 0.3:
            confidence += 0.2
        elif velocity > 0.1:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'sentiment_volume_threshold': self.sentiment_volume_threshold
        }
