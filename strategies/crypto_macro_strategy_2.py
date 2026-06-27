"""
AlphaEdge Strategy – Crypto Macro Strategy 2
Monitors global liquidity and risk appetite for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy2:
    """
    Crypto Macro Strategy 2
    Uses global liquidity and risk appetite to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_2"
        self.name = "Crypto Macro Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.global_liquidity_threshold = 70
        self.risk_appetite_threshold = 60
        self.vix_threshold = 25
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        global_liquidity = data.get('global_liquidity', 50)
        risk_appetite = data.get('risk_appetite', 50)
        vix = data.get('vix', 20)
        
        # Check conditions
        if global_liquidity >= self.global_liquidity_threshold:
            if risk_appetite >= self.risk_appetite_threshold:
                if vix < self.vix_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(global_liquidity, risk_appetite, vix),
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
        
    def calculate_confidence(self, global_liquidity: float, risk_appetite: float, vix: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Global liquidity (0-0.4)
        confidence += (global_liquidity - 50) / 100 * 0.4
        
        # Risk appetite (0-0.4)
        confidence += (risk_appetite - 50) / 100 * 0.4
        
        # VIX (0-0.2)
        if vix < 20:
            confidence += 0.2
        elif vix < 25:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'global_liquidity_threshold': self.global_liquidity_threshold,
            'risk_appetite_threshold': self.risk_appetite_threshold,
            'vix_threshold': self.vix_threshold
        }
