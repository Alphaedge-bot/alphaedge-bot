"""
AlphaEdge Strategy – Crypto Macro Strategy 9
Monitors global trade and currency flows for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy9:
    """
    Crypto Macro Strategy 9
    Uses global trade and currency flows to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_9"
        self.name = "Crypto Macro Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.trade_balance_threshold = 50  # 50B surplus
        self.currency_flow_threshold = 100  # 100B flow
        self.dollar_index_threshold = 100
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        trade_balance = data.get('trade_balance', 0)
        currency_flow = data.get('currency_flow', 0)
        dollar_index = data.get('dollar_index', 0)
        
        # Check conditions
        if trade_balance >= self.trade_balance_threshold:
            if currency_flow >= self.currency_flow_threshold:
                if dollar_index <= self.dollar_index_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(trade_balance, currency_flow, dollar_index),
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
        
    def calculate_confidence(self, trade_balance: float, currency_flow: float, dollar_index: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Trade balance (0-0.35)
        if trade_balance > 80:
            confidence += 0.35
        elif trade_balance > 50:
            confidence += 0.15
            
        # Currency flow (0-0.35)
        if currency_flow > 150:
            confidence += 0.35
        elif currency_flow > 100:
            confidence += 0.15
            
        # Dollar index (0-0.3)
        if dollar_index < 90:
            confidence += 0.3
        elif dollar_index < 100:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'trade_balance_threshold': self.trade_balance_threshold,
            'currency_flow_threshold': self.currency_flow_threshold,
            'dollar_index_threshold': self.dollar_index_threshold
        }
