"""
AlphaEdge Strategy – Liquidation Cascade Strategy 6
Perpetual futures and options liquidation analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LiquidationCascadeStrategy6:
    """
    Liquidation Cascade Strategy 6
    Analyzes perpetual futures and options liquidations
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "liquidation_cascade_6"
        self.name = "Liquidation Cascade Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.perp_liquidation_threshold = 100000  # $100K
        self.option_liquidation_threshold = 50000  # $50K
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        perp_liquidations = data.get('perp_liquidations', 0)
        option_liquidations = data.get('option_liquidations', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for liquidation risk
        if perp_liquidations > self.perp_liquidation_threshold:
            if option_liquidations > self.option_liquidation_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'watch',
                        'confidence': self.calculate_confidence(perp_liquidations, option_liquidations),
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
        
    def calculate_confidence(self, perp_liquidations: float, option_liquidations: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Perp liquidations
        if perp_liquidations > 500000:
            confidence += 0.2
        elif perp_liquidations > 100000:
            confidence += 0.1
            
        # Option liquidations
        if option_liquidations > 200000:
            confidence += 0.2
        elif option_liquidations > 50000:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'perp_liquidation_threshold': self.perp_liquidation_threshold
        }
