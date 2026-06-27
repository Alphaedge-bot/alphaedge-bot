"""
AlphaEdge Strategy – Crypto Macro Strategy 14
Monitors cryptocurrency regulation and policy for signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy14:
    """
    Crypto Macro Strategy 14
    Uses regulatory sentiment and policy to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_14"
        self.name = "Crypto Macro Strategy 14"
        self.active = True
        
        # Strategy parameters
        self.regulatory_sentiment_threshold = 50
        self.policy_clarity_threshold = 50
        self.adoption_rate_threshold = 2.0  # 2% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        regulatory_sentiment = data.get('regulatory_sentiment', 50)
        policy_clarity = data.get('policy_clarity', 50)
        adoption_rate = data.get('adoption_rate', 0)
        
        # Check conditions
        if regulatory_sentiment >= self.regulatory_sentiment_threshold:
            if policy_clarity >= self.policy_clarity_threshold:
                if adoption_rate >= self.adoption_rate_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(regulatory_sentiment, policy_clarity, adoption_rate),
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
        
    def calculate_confidence(self, regulatory_sentiment: float, policy_clarity: float, adoption_rate: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Regulatory sentiment (0-0.35)
        confidence += (regulatory_sentiment - 50) / 100 * 0.35
        
        # Policy clarity (0-0.35)
        confidence += (policy_clarity - 50) / 100 * 0.35
        
        # Adoption rate (0-0.3)
        if adoption_rate > 3.0:
            confidence += 0.3
        elif adoption_rate > 2.0:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'regulatory_sentiment_threshold': self.regulatory_sentiment_threshold,
            'policy_clarity_threshold': self.policy_clarity_threshold,
            'adoption_rate_threshold': self.adoption_rate_threshold
        }
