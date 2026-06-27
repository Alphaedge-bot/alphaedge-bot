"""
AlphaEdge Strategy – Crypto Macro Strategy 6
Monitors geopolitical risk and safe haven flows for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy6:
    """
    Crypto Macro Strategy 6
    Uses geopolitical risk and safe haven flows to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_6"
        self.name = "Crypto Macro Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.geopolitical_risk_threshold = 30
        self.safe_haven_flow_threshold = 50
        self.gold_price_trend_threshold = 0.5
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        geopolitical_risk = data.get('geopolitical_risk', 50)
        safe_haven_flow = data.get('safe_haven_flow', 50)
        gold_trend = data.get('gold_price_trend', 0)
        
        # Check conditions
        if geopolitical_risk <= self.geopolitical_risk_threshold:
            if safe_haven_flow >= self.safe_haven_flow_threshold:
                if gold_trend >= self.gold_price_trend_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(geopolitical_risk, safe_haven_flow, gold_trend),
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
        
    def calculate_confidence(self, geopolitical_risk: float, safe_haven_flow: float, gold_trend: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Geopolitical risk (0-0.4)
        if geopolitical_risk < 20:
            confidence += 0.4
        elif geopolitical_risk < 30:
            confidence += 0.2
            
        # Safe haven flow (0-0.4)
        confidence += (safe_haven_flow - 50) / 100 * 0.4
        
        # Gold trend (0-0.2)
        if gold_trend > 1.0:
            confidence += 0.2
        elif gold_trend > 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'geopolitical_risk_threshold': self.geopolitical_risk_threshold,
            'safe_haven_flow_threshold': self.safe_haven_flow_threshold,
            'gold_price_trend_threshold': self.gold_price_trend_threshold
        }
