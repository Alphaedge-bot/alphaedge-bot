"""
AlphaEdge Strategy – ICT/SMC Strategy 1
Order block detection and FVG (Fair Value Gap) trading
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ICTSMCStrategy1:
    """
    ICT/SMC Strategy 1
    Uses Order Blocks and Fair Value Gaps for entry signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ict_smc_1"
        self.name = "ICT/SMC Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.fvg_threshold = 0.005  # 0.5%
        self.ob_strength_threshold = 0.02  # 2%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        fvg_low = data.get('fvg_low', 0)
        fvg_high = data.get('fvg_high', 0)
        ob_zone = data.get('ob_zone', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for FVG fill (buy)
        if fvg_low > 0 and fvg_high > 0:
            if price >= fvg_low and price <= fvg_high:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(price, fvg_low, fvg_high, ob_zone, volume_ratio),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for Order Block bounce (buy)
        if ob_zone > 0 and abs(price - ob_zone) / ob_zone < self.ob_strength_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, fvg_low, fvg_high, ob_zone, volume_ratio),
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
        
    def calculate_confidence(self, price: float, fvg_low: float, fvg_high: float, ob_zone: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # FVG fill
        if fvg_low > 0 and fvg_high > 0:
            if price >= fvg_low and price <= fvg_high:
                confidence += 0.2
                
        # OB proximity
        if ob_zone > 0:
            ob_proximity = abs(price - ob_zone) / ob_zone
            if ob_proximity < 0.01:
                confidence += 0.2
            elif ob_proximity < 0.02:
                confidence += 0.1
                
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
