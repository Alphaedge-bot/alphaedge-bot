"""
AlphaEdge Strategy – Market Sentiment Strategy 6
Retail vs institutional sentiment divergence
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketSentimentStrategy6:
    """
    Market Sentiment Strategy 6
    Analyzes retail vs institutional sentiment divergence
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "market_sentiment_6"
        self.name = "Market Sentiment Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.divergence_threshold = 0.2  # 20%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        retail_sentiment = data.get('retail_sentiment', 0.5)
        institutional_sentiment = data.get('institutional_sentiment', 0.5)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate divergence
        divergence = retail_sentiment - institutional_sentiment
        
        # Check for retail bullish / institutional bearish divergence
        if divergence > self.divergence_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(divergence, 'retail'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for institutional bullish / retail bearish divergence
        elif divergence < -self.divergence_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(divergence, 'institutional'),
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
        
    def calculate_confidence(self, divergence: float, type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Divergence strength
        if abs(divergence) > 0.4:
            confidence += 0.3
        elif abs(divergence) > 0.2:
            confidence += 0.15
            
        # Type specific confidence
        if type == 'institutional':
            confidence += 0.15
        elif type == 'retail':
            confidence += 0.05
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'divergence_threshold': self.divergence_threshold
        }
