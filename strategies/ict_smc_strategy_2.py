"""
AlphaEdge Strategy – ICT/SMC Strategy 2
Market structure shift (MSS) and liquidity sweep detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ICTSMCStrategy2:
    """
    ICT/SMC Strategy 2
    Uses Market Structure Shifts and Liquidity Sweeps
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ict_smc_2"
        self.name = "ICT/SMC Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.mss_threshold = 0.01  # 1%
        self.liquidity_sweep_threshold = 0.005  # 0.5%
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
        mss_detected = data.get('mss_detected', False)
        liquidity_sweep = data.get('liquidity_sweep', False)
        prev_high = data.get('prev_high', 0)
        prev_low = data.get('prev_low', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for MSS (buy)
        if mss_detected and volume_ratio > self.volume_confirm:
            if price > prev_high:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(mss_detected, liquidity_sweep, price, prev_high, prev_low),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for liquidity sweep (buy)
        elif liquidity_sweep and volume_ratio > self.volume_confirm:
            if price > prev_low:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(mss_detected, liquidity_sweep, price, prev_high, prev_low),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for MSS (sell)
        elif mss_detected and volume_ratio > self.volume_confirm:
            if price < prev_low:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(mss_detected, liquidity_sweep, price, prev_high, prev_low),
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
        
    def calculate_confidence(self, mss_detected: bool, liquidity_sweep: bool, price: float, prev_high: float, prev_low: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # MSS confirmation
        if mss_detected:
            confidence += 0.2
            
        # Liquidity sweep confirmation
        if liquidity_sweep:
            confidence += 0.2
            
        # Breakout strength
        if prev_high > 0 and price > prev_high:
            breakout_pct = (price - prev_high) / prev_high
            if breakout_pct > 0.02:
                confidence += 0.1
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active
        }
