"""
AlphaEdge Strategy – Crypto Macro Strategy 11
Monitors housing market and consumer confidence for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy11:
    """
    Crypto Macro Strategy 11
    Uses housing market and consumer confidence to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_11"
        self.name = "Crypto Macro Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.housing_start_threshold = 1000000  # 1M housing starts
        self.consumer_confidence_threshold = 100
        self.housing_price_threshold = 0.5  # 0.5% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        housing_starts = data.get('housing_starts', 0)
        consumer_confidence = data.get('consumer_confidence', 0)
        housing_price = data.get('housing_price_growth', 0)
        
        # Check conditions
        if housing_starts >= self.housing_start_threshold:
            if consumer_confidence >= self.consumer_confidence_threshold:
                if housing_price >= self.housing_price_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(housing_starts, consumer_confidence, housing_price),
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
        
    def calculate_confidence(self, housing_starts: float, consumer_confidence: float, housing_price: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Housing starts (0-0.35)
        if housing_starts > 1200000:
            confidence += 0.35
        elif housing_starts > 1000000:
            confidence += 0.15
            
        # Consumer confidence (0-0.35)
        if consumer_confidence > 120:
            confidence += 0.35
        elif consumer_confidence > 100:
            confidence += 0.15
            
        # Housing price (0-0.3)
        if housing_price > 1.0:
            confidence += 0.3
        elif housing_price > 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'housing_start_threshold': self.housing_start_threshold,
            'consumer_confidence_threshold': self.consumer_confidence_threshold,
            'housing_price_threshold': self.housing_price_threshold
        }
