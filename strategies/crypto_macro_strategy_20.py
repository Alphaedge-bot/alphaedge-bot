"""
AlphaEdge Strategy – Crypto Macro Strategy 20
Monitors crypto sentiment and social media for signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy20:
    """
    Crypto Macro Strategy 20
    Uses sentiment and social media to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_20"
        self.name = "Crypto Macro Strategy 20"
        self.active = True
        
        # Strategy parameters
        self.sentiment_threshold = 60
        self.social_volume_threshold = 10000
        self.sentiment_trend_threshold = 2.0  # 2% change
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        sentiment = data.get('sentiment_score', 50)
        social_volume = data.get('social_volume', 0)
        sentiment_trend = data.get('sentiment_trend', 0)
        
        # Check conditions
        if sentiment >= self.sentiment_threshold:
            if social_volume >= self.social_volume_threshold:
                if sentiment_trend >= self.sentiment_trend_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(sentiment, social_volume, sentiment_trend),
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
        
    def calculate_confidence(self, sentiment: float, social_volume: float, sentiment_trend: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sentiment (0-0.35)
        if sentiment > 70:
            confidence += 0.35
        elif sentiment > 60:
            confidence += 0.15
            
        # Social volume (0-0.35)
        if social_volume > 20000:
            confidence += 0.35
        elif social_volume > 10000:
            confidence += 0.15
            
        # Sentiment trend (0-0.3)
        if sentiment_trend > 4.0:
            confidence += 0.3
        elif sentiment_trend > 2.0:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'sentiment_threshold': self.sentiment_threshold,
            'social_volume_threshold': self.social_volume_threshold,
            'sentiment_trend_threshold': self.sentiment_trend_threshold
        }
