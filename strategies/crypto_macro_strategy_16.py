"""
AlphaEdge Strategy – Crypto Macro Strategy 16
Monitors stablecoin supply and DeFi growth for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy16:
    """
    Crypto Macro Strategy 16
    Uses stablecoin supply and DeFi growth to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_16"
        self.name = "Crypto Macro Strategy 16"
        self.active = True
        
        # Strategy parameters
        self.stablecoin_supply_threshold = 100000000000  # $100B
        self.defi_tvl_threshold = 50000000000  # $50B
        self.defi_growth_threshold = 5.0  # 5% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        stablecoin_supply = data.get('stablecoin_supply', 0)
        defi_tvl = data.get('defi_tvl', 0)
        defi_growth = data.get('defi_growth', 0)
        
        # Check conditions
        if stablecoin_supply >= self.stablecoin_supply_threshold:
            if defi_tvl >= self.defi_tvl_threshold:
                if defi_growth >= self.defi_growth_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(stablecoin_supply, defi_tvl, defi_growth),
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
        
    def calculate_confidence(self, stablecoin_supply: float, defi_tvl: float, defi_growth: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Stablecoin supply (0-0.35)
        if stablecoin_supply > 150000000000:
            confidence += 0.35
        elif stablecoin_supply > 100000000000:
            confidence += 0.15
            
        # DeFi TVL (0-0.35)
        if defi_tvl > 75000000000:
            confidence += 0.35
        elif defi_tvl > 50000000000:
            confidence += 0.15
            
        # DeFi growth (0-0.3)
        if defi_growth > 8.0:
            confidence += 0.3
        elif defi_growth > 5.0:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'stablecoin_supply_threshold': self.stablecoin_supply_threshold,
            'defi_tvl_threshold': self.defi_tvl_threshold,
            'defi_growth_threshold': self.defi_growth_threshold
        }
