"""
AlphaEdge Strategy – Crypto Macro Strategy 19
Monitors crypto derivatives and futures markets for signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy19:
    """
    Crypto Macro Strategy 19
    Uses derivatives and futures markets to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_19"
        self.name = "Crypto Macro Strategy 19"
        self.active = True
        
        # Strategy parameters
        self.futures_oi_threshold = 10000000000  # $10B
        self.funding_rate_threshold = 0.01  # 0.01%
        self.options_volume_threshold = 1000000000  # $1B
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        futures_oi = data.get('futures_oi', 0)
        funding_rate = data.get('funding_rate', 0)
        options_volume = data.get('options_volume', 0)
        
        # Check conditions
        if futures_oi >= self.futures_oi_threshold:
            if funding_rate <= self.funding_rate_threshold:
                if options_volume >= self.options_volume_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(futures_oi, funding_rate, options_volume),
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
        
    def calculate_confidence(self, futures_oi: float, funding_rate: float, options_volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Futures OI (0-0.35)
        if futures_oi > 15000000000:
            confidence += 0.35
        elif futures_oi > 10000000000:
            confidence += 0.15
            
        # Funding rate (0-0.35)
        if funding_rate < 0.005:
            confidence += 0.35
        elif funding_rate < 0.01:
            confidence += 0.15
            
        # Options volume (0-0.3)
        if options_volume > 1500000000:
            confidence += 0.3
        elif options_volume > 1000000000:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'futures_oi_threshold': self.futures_oi_threshold,
            'funding_rate_threshold': self.funding_rate_threshold,
            'options_volume_threshold': self.options_volume_threshold
        }
