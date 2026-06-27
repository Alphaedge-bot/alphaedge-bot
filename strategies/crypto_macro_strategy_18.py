"""
AlphaEdge Strategy – Crypto Macro Strategy 18
Monitors crypto exchange flows and liquidity for signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy18:
    """
    Crypto Macro Strategy 18
    Uses exchange flows and liquidity to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_18"
        self.name = "Crypto Macro Strategy 18"
        self.active = True
        
        # Strategy parameters
        self.exchange_inflow_threshold = 1000000  # $1M
        self.exchange_outflow_threshold = 1000000  # $1M
        self.order_book_depth_threshold = 1000000  # $1M
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        exchange_inflow = data.get('exchange_inflow', 0)
        exchange_outflow = data.get('exchange_outflow', 0)
        order_book_depth = data.get('order_book_depth', 0)
        
        # Check conditions
        if exchange_inflow >= self.exchange_inflow_threshold:
            if exchange_outflow >= self.exchange_outflow_threshold:
                if order_book_depth >= self.order_book_depth_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(exchange_inflow, exchange_outflow, order_book_depth),
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
        
    def calculate_confidence(self, exchange_inflow: float, exchange_outflow: float, order_book_depth: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Exchange inflow (0-0.25)
        if exchange_inflow > 2000000:
            confidence += 0.25
        elif exchange_inflow > 1000000:
            confidence += 0.10
            
        # Exchange outflow (0-0.35)
        if exchange_outflow > 2000000:
            confidence += 0.35
        elif exchange_outflow > 1000000:
            confidence += 0.15
            
        # Order book depth (0-0.4)
        if order_book_depth > 2000000:
            confidence += 0.4
        elif order_book_depth > 1000000:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'exchange_inflow_threshold': self.exchange_inflow_threshold,
            'exchange_outflow_threshold': self.exchange_outflow_threshold,
            'order_book_depth_threshold': self.order_book_depth_threshold
        }
