"""
AlphaEdge Strategy – Market Sentiment Strategy 3
Google Trends and retail interest analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketSentimentStrategy3:
    """
    Market Sentiment Strategy 3
    Analyzes Google Trends and retail interest
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "market_sentiment_3"
        self.name = "Market Sentiment Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.trends_threshold = 50
        self.interest_change_threshold = 0.2  # 20%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        google_trends = data.get('google_trends', 0)
        interest_change = data.get('interest_change', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for rising retail interest
        if google_trends > self.trends_threshold:
            if interest_change > self.interest_change_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(google_trends, interest_change),
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
        
    def calculate_confidence(self, trends: float, interest_change: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Google Trends
        if trends > 80:
            confidence += 0.2
        elif trends > 50:
            confidence += 0.1
            
        # Interest change
        if interest_change > 0.5:
            confidence += 0.2
        elif interest_change > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'trends_threshold': self.trends_threshold
        }
