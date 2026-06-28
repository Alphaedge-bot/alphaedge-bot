"""
AlphaEdge Strategy – Solana Specific Strategy 11
Solana ecosystem token metrics and performance
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SolanaSpecificStrategy11:
    """
    Solana Specific Strategy 11
    Analyzes Solana ecosystem token metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "solana_specific_11"
        self.name = "Solana Specific Strategy 11"
        self.active = True
        
        # Strategy parameters
        self.token_market_cap_threshold = 100000000  # $100M
        self.token_volume_threshold = 1000000  # $1M
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        token_market_cap = data.get('solana_token_market_cap', 0)
        token_volume = data.get('solana_token_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for token performance signal
        if token_market_cap > self.token_market_cap_threshold:
            if token_volume > self.token_volume_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'token_performance',
                        'confidence': self.calculate_confidence(token_market_cap, token_volume),
                        'token_market_cap': token_market_cap,
                        'token_volume': token_volume,
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
        
    def calculate_confidence(self, market_cap: float, volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Market cap
        if market_cap > 500000000:
            confidence += 0.2
        elif market_cap > 100000000:
            confidence += 0.1
            
        # Volume
        if volume > 5000000:
            confidence += 0.2
        elif volume > 1000000:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'token_market_cap_threshold': self.token_market_cap_threshold,
            'token_volume_threshold': self.token_volume_threshold
        }
