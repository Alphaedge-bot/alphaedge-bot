"""
AlphaEdge Strategy – Crypto Macro Strategy 4
Monitors market sentiment and positioning for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy4:
    """
    Crypto Macro Strategy 4
    Uses market sentiment and positioning to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_4"
        self.name = "Crypto Macro Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.sentiment_threshold = 60
        self.positioning_threshold = 60
        self.fear_greed_threshold = 30  # Below 30 = Fear, above 70 = Greed
        
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
        positioning = data.get('positioning_score', 50)
        fear_greed = data.get('fear_greed_index', 50)
        
        # Check conditions
        if sentiment >= self.sentiment_threshold:
            if positioning >= self.positioning_threshold:
                if fear_greed <= self.fear_greed_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(sentiment, positioning, fear_greed),
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
        
    def calculate_confidence(self, sentiment: float, positioning: float, fear_greed: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sentiment (0-0.4)
        confidence += (sentiment - 50) / 100 * 0.4
        
        # Positioning (0-0.4)
        confidence += (positioning - 50) / 100 * 0.4
        
        # Fear & Greed (0-0.2)
        if fear_greed < 20:
            confidence += 0.2
        elif fear_greed < 30:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'sentiment_threshold': self.sentiment_threshold,
            'positioning_threshold': self.positioning_threshold,
            'fear_greed_threshold': self.fear_greed_threshold
        }
