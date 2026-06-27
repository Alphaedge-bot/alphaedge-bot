"""
AlphaEdge Strategy – AI/ML Signals Strategy 3
Transformer attention mechanism for market patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AIMLSignalsStrategy3:
    """
    AI/ML Signals Strategy 3
    Uses Transformer attention for market pattern detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ai_ml_signals_3"
        self.name = "AI/ML Signals Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.attention_threshold = 0.5
        self.pattern_confidence = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        attention_scores = data.get('attention_scores', [])
        pattern = data.get('transformer_pattern', 'none')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if attention scores indicate pattern
        if attention_scores:
            avg_attention = sum(attention_scores) / len(attention_scores)
            
            if avg_attention > self.attention_threshold:
                if pattern == 'bullish' and avg_attention > self.attention_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'buy',
                            'confidence': self.calculate_confidence(avg_attention, pattern),
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
        
    def calculate_confidence(self, attention: float, pattern: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Attention strength
        if attention > 0.7:
            confidence += 0.2
        elif attention > 0.5:
            confidence += 0.1
            
        # Pattern confidence
        if pattern == 'bullish':
            confidence += 0.2
        elif pattern == 'bearish':
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'attention_threshold': self.attention_threshold
        }
