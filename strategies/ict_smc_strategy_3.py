"""
AlphaEdge Strategy – ICT/SMC Strategy 3
PD Array and Fibonacci confluence zones
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ICTSMCStrategy3:
    """
    ICT/SMC Strategy 3
    Uses PD Arrays and Fibonacci confluence zones
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ict_smc_3"
        self.name = "ICT/SMC Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.fib_levels = [0.618, 0.786]
        self.pd_array_threshold = 0.01  # 1%
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
        pd_array = data.get('pd_array', 0)
        fib_confluence = data.get('fib_confluence', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for PD Array confluence (buy)
        if pd_array > 0 and abs(price - pd_array) / pd_array < self.pd_array_threshold:
            if fib_confluence > 0 and abs(price - fib_confluence) / fib_confluence < self.pd_array_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(price, pd_array, fib_confluence, volume_ratio),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for PD Array only
        elif pd_array > 0 and abs(price - pd_array) / pd_array < self.pd_array_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'watch',
                    'confidence': 0.5,
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
        
    def calculate_confidence(self, price: float, pd_array: float, fib_confluence: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # PD Array confirmation
        if pd_array > 0:
            pd_proximity = abs(price - pd_array) / pd_array
            if pd_proximity < 0.005:
                confidence += 0.2
            elif pd_proximity < 0.01:
                confidence += 0.1
                
        # Fibonacci confluence
        if fib_confluence > 0:
            fib_proximity = abs(price - fib_confluence) / fib_confluence
            if fib_proximity < 0.005:
                confidence += 0.2
            elif fib_proximity < 0.01:
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
            'active': self.active,
            'fib_levels': self.fib_levels
        }
