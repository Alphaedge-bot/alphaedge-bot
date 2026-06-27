"""
AlphaEdge Strategy – Crypto Macro Strategy 3
Monitors Fed policy and interest rates for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy3:
    """
    Crypto Macro Strategy 3
    Uses Fed policy and interest rates to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_3"
        self.name = "Crypto Macro Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.fed_rate_threshold = 2.5  # 2.5%
        self.fed_policy_threshold = 50  # 0-100 scale
        self.yield_curve_threshold = 0.5  # 0.5% spread
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        fed_rate = data.get('fed_rate', 0)
        fed_policy = data.get('fed_policy', 50)
        yield_curve = data.get('yield_curve', 0)
        
        # Check conditions
        if fed_rate <= self.fed_rate_threshold:
            if fed_policy >= self.fed_policy_threshold:
                if yield_curve >= self.yield_curve_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(fed_rate, fed_policy, yield_curve),
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
        
    def calculate_confidence(self, fed_rate: float, fed_policy: float, yield_curve: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fed rate (0-0.35)
        if fed_rate < 1.0:
            confidence += 0.35
        elif fed_rate < 2.0:
            confidence += 0.2
        else:
            confidence += 0.1
            
        # Fed policy (0-0.35)
        confidence += (fed_policy - 50) / 100 * 0.35
        
        # Yield curve (0-0.3)
        if yield_curve > 1.0:
            confidence += 0.3
        elif yield_curve > 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'fed_rate_threshold': self.fed_rate_threshold,
            'fed_policy_threshold': self.fed_policy_threshold,
            'yield_curve_threshold': self.yield_curve_threshold
        }
