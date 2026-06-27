"""
AlphaEdge Strategy – Crypto Macro Strategy 12
Monitors manufacturing and industrial production for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy12:
    """
    Crypto Macro Strategy 12
    Uses manufacturing and industrial production to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_12"
        self.name = "Crypto Macro Strategy 12"
        self.active = True
        
        # Strategy parameters
        self.pmi_threshold = 50  # PMI > 50 = expansion
        self.industrial_production_threshold = 2.0  # 2% growth
        self.factory_orders_threshold = 0.5  # 0.5% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        pmi = data.get('pmi', 0)
        industrial_production = data.get('industrial_production', 0)
        factory_orders = data.get('factory_orders', 0)
        
        # Check conditions
        if pmi >= self.pmi_threshold:
            if industrial_production >= self.industrial_production_threshold:
                if factory_orders >= self.factory_orders_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(pmi, industrial_production, factory_orders),
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
        
    def calculate_confidence(self, pmi: float, industrial_production: float, factory_orders: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # PMI (0-0.35)
        if pmi > 55:
            confidence += 0.35
        elif pmi > 50:
            confidence += 0.15
            
        # Industrial production (0-0.35)
        if industrial_production > 3.0:
            confidence += 0.35
        elif industrial_production > 2.0:
            confidence += 0.15
            
        # Factory orders (0-0.3)
        if factory_orders > 1.0:
            confidence += 0.3
        elif factory_orders > 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pmi_threshold': self.pmi_threshold,
            'industrial_production_threshold': self.industrial_production_threshold,
            'factory_orders_threshold': self.factory_orders_threshold
        }
