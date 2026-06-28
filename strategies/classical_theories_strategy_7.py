"""
AlphaEdge Strategy – Classical Theories Strategy 7
Swing trading and retracement patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ClassicalTheoriesStrategy7:
    """
    Classical Theories Strategy 7
    Identifies swing trading and retracement patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "classical_theories_7"
        self.name = "Classical Theories Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.swing_threshold = 0.03  # 3%
        self.retracement_threshold = 0.5  # 50%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        price = data.get('price', 0)
        swing_high = data.get('swing_high', price)
        swing_low = data.get('swing_low', price)
        retracement = data.get('retracement', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for swing low bounce (buy)
        if swing_low > 0 and price > swing_low * (1 + self.swing_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(price, swing_high, swing_low, retracement),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for swing high rejection (sell)
        elif swing_high > 0 and price < swing_high * (1 - self.swing_threshold):
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(price, swing_high, swing_low, retracement),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check for 50% retracement
        if retracement > 0 and retracement < self.retracement_threshold:
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
        
    def calculate_confidence(self, price: float, swing_high: float, swing_low: float, retracement: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Swing strength
        if swing_high > 0 and swing_low > 0:
            swing_range = (swing_high - swing_low) / swing_low
            if swing_range > 0.1:
                confidence += 0.2
            elif swing_range > 0.05:
                confidence += 0.1
                
        # Retracement
        if retracement > 0 and retracement < 0.5:
            confidence += 0.1
            
        # Price position
        if swing_high > 0 and swing_low > 0:
            position = (price - swing_low) / (swing_high - swing_low) if swing_high != swing_low else 0.5
            if 0.2 < position < 0.8:
                confidence += 0.1
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'swing_threshold': self.swing_threshold,
            'retracement_threshold': self.retracement_threshold
        }
