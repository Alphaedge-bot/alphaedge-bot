"""
AlphaEdge Strategy – Crypto Macro Strategy 15
Monitors institutional adoption and investment flows for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy15:
    """
    Crypto Macro Strategy 15
    Uses institutional adoption and investment flows to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_15"
        self.name = "Crypto Macro Strategy 15"
        self.active = True
        
        # Strategy parameters
        self.institutional_flow_threshold = 1000000000  # $1B
        self.etf_flow_threshold = 500000000  # $500M
        self.adoption_rate_threshold = 2.0  # 2% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        institutional_flow = data.get('institutional_flow', 0)
        etf_flow = data.get('etf_flow', 0)
        adoption_rate = data.get('adoption_rate', 0)
        
        # Check conditions
        if institutional_flow >= self.institutional_flow_threshold:
            if etf_flow >= self.etf_flow_threshold:
                if adoption_rate >= self.adoption_rate_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(institutional_flow, etf_flow, adoption_rate),
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
        
    def calculate_confidence(self, institutional_flow: float, etf_flow: float, adoption_rate: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Institutional flow (0-0.35)
        if institutional_flow > 2000000000:
            confidence += 0.35
        elif institutional_flow > 1000000000:
            confidence += 0.15
            
        # ETF flow (0-0.35)
        if etf_flow > 1000000000:
            confidence += 0.35
        elif etf_flow > 500000000:
            confidence += 0.15
            
        # Adoption rate (0-0.3)
        if adoption_rate > 3.0:
            confidence += 0.3
        elif adoption_rate > 2.0:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'institutional_flow_threshold': self.institutional_flow_threshold,
            'etf_flow_threshold': self.etf_flow_threshold,
            'adoption_rate_threshold': self.adoption_rate_threshold
        }
