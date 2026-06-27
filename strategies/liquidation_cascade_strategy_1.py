"""
AlphaEdge Strategy – Liquidation Cascade Strategy 1
Leverage ratio monitoring and cascade detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LiquidationCascadeStrategy1:
    """
    Liquidation Cascade Strategy 1
    Monitors leverage ratios for cascade detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "liquidation_cascade_1"
        self.name = "Liquidation Cascade Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.leverage_threshold = 10  # 10x leverage
        self.cascade_trigger = 0.05   # 5% price move
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        avg_leverage = data.get('avg_leverage', 0)
        price_change = data.get('price_change', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high leverage risk
        if avg_leverage > self.leverage_threshold:
            if abs(price_change) > self.cascade_trigger:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'watch',
                        'confidence': self.calculate_confidence(avg_leverage, price_change),
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
        
    def calculate_confidence(self, leverage: float, price_change: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Leverage risk
        if leverage > 20:
            confidence += 0.3
        elif leverage > 10:
            confidence += 0.15
            
        # Price movement
        if abs(price_change) > 0.1:
            confidence += 0.2
        elif abs(price_change) > 0.05:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'leverage_threshold': self.leverage_threshold
        }
