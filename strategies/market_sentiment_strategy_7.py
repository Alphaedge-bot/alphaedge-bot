"""
AlphaEdge Strategy – Market Sentiment Strategy 7
News sentiment and headline analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketSentimentStrategy7:
    """
    Market Sentiment Strategy 7
    Analyzes news sentiment and headlines
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "market_sentiment_7"
        self.name = "Market Sentiment Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.news_sentiment_threshold = 0.6
        self.headline_volume_threshold = 100
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        news_sentiment = data.get('news_sentiment', 0.5)
        headline_volume = data.get('headline_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for positive news (buy)
        if news_sentiment > self.news_sentiment_threshold:
            if headline_volume > self.headline_volume_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(news_sentiment, headline_volume),
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
        
    def calculate_confidence(self, news_sentiment: float, headline_volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # News sentiment
        if news_sentiment > 0.8:
            confidence += 0.2
        elif news_sentiment > 0.6:
            confidence += 0.1
            
        # Headline volume
        if headline_volume > 500:
            confidence += 0.2
        elif headline_volume > 100:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'news_sentiment_threshold': self.news_sentiment_threshold
        }
