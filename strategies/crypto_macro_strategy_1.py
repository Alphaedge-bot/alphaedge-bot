"""
AlphaEdge Strategy – Crypto Macro Strategy 1
Monitors macro-economic conditions for crypto trading signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy1:
    """
    Crypto Macro Strategy 1
    Uses macro indicators to generate trading signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_1"
        self.name = "Crypto Macro Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.fed_liquidity_threshold = 60
        self.dxy_threshold = 100
        self.regime_preferences = ['bull', 'alt', 'accumulation']
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        fed_liquidity_score = data.get('fed_liquidity', {}).get('score', 50)
        dxy = data.get('dxy', {}).get('price', 0)
        regime = data.get('regime', 'neutral')
        
        # Check if conditions are favorable
        if fed_liquidity_score >= self.fed_liquidity_threshold:
            if dxy < self.dxy_threshold:
                if regime in self.regime_preferences:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(fed_liquidity_score, dxy),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Publish signal
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
    async def handle_signal_request(self, event: Event):
        """Handle signal requests"""
        # Return current signal
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
        
    def calculate_confidence(self, fed_liquidity: float, dxy: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fed liquidity contribution (0-0.5)
        confidence += (fed_liquidity - 50) / 100 * 0.5
        
        # DXY contribution (0-0.3)
        if dxy < 100:
            confidence += (100 - dxy) / 100 * 0.3
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'fed_liquidity_threshold': self.fed_liquidity_threshold,
            'dxy_threshold': self.dxy_threshold
        }
