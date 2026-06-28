"""
AlphaEdge Strategy – Marketing Ambiguity Strategy 1
Market narrative and sentiment detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketingAmbiguityStrategy1:
    """
    Marketing Ambiguity Strategy 1
    Detects market narratives and sentiment
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "marketing_ambiguity_1"
        self.name = "Marketing Ambiguity Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.narrative_threshold = 0.5
        self.sentiment_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        market_narrative = data.get('market_narrative', 'neutral')
        sentiment_score = data.get('sentiment_score', 0.5)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for strong narrative
        if sentiment_score > self.sentiment_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'narrative_signal',
                    'confidence': self.calculate_confidence(sentiment_score, market_narrative),
                    'narrative': market_narrative,
                    'sentiment_score': sentiment_score,
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
        
    def calculate_confidence(self, sentiment_score: float, narrative: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Sentiment score
        if sentiment_score > 0.8:
            confidence += 0.2
        elif sentiment_score > 0.6:
            confidence += 0.1
            
        # Narrative strength
        if narrative in ['bullish', 'optimistic']:
            confidence += 0.2
        elif narrative in ['neutral']:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'narrative_threshold': self.narrative_threshold,
            'sentiment_threshold': self.sentiment_threshold
        }
