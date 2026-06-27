"""
AlphaEdge Strategy – Crypto Macro Strategy 7
Monitors commodity prices and supply chain for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy7:
    """
    Crypto Macro Strategy 7
    Uses commodity prices and supply chain to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_7"
        self.name = "Crypto Macro Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.oil_price_threshold = 70  # USD per barrel
        self.copper_price_threshold = 4.0  # USD per pound
        self.supply_chain_index_threshold = 50
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        oil_price = data.get('oil_price', 0)
        copper_price = data.get('copper_price', 0)
        supply_chain_index = data.get('supply_chain_index', 50)
        
        # Check conditions
        if oil_price <= self.oil_price_threshold:
            if copper_price >= self.copper_price_threshold:
                if supply_chain_index >= self.supply_chain_index_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(oil_price, copper_price, supply_chain_index),
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
        
    def calculate_confidence(self, oil_price: float, copper_price: float, supply_chain_index: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Oil price (0-0.35)
        if oil_price < 60:
            confidence += 0.35
        elif oil_price < 70:
            confidence += 0.15
            
        # Copper price (0-0.35)
        if copper_price > 4.5:
            confidence += 0.35
        elif copper_price > 4.0:
            confidence += 0.15
            
        # Supply chain (0-0.3)
        confidence += (supply_chain_index - 50) / 100 * 0.3
        
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'oil_price_threshold': self.oil_price_threshold,
            'copper_price_threshold': self.copper_price_threshold,
            'supply_chain_index_threshold': self.supply_chain_index_threshold
        }
