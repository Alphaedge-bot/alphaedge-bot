"""
AlphaEdge Strategy – Technical TA Strategy 25
Synthetic composite indicator combining multiple TA signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy25:
    """
    Technical TA Strategy 25
    Uses synthetic composite indicator combining multiple TA signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_25"
        self.name = "Technical TA Strategy 25"
        self.active = True
        
        # Strategy parameters
        self.signal_weights = {
            'rsi': 0.25,
            'macd': 0.25,
            'ma': 0.20,
            'volume': 0.15,
            'bb': 0.15
        }
        self.composite_threshold = 0.6
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        rsi_signal = data.get('rsi_signal', 0)
        macd_signal = data.get('macd_signal', 0)
        ma_signal = data.get('ma_signal', 0)
        volume_signal = data.get('volume_signal', 0)
        bb_signal = data.get('bb_signal', 0)
        
        # Calculate composite signal
        composite = (
            rsi_signal * self.signal_weights['rsi'] +
            macd_signal * self.signal_weights['macd'] +
            ma_signal * self.signal_weights['ma'] +
            volume_signal * self.signal_weights['volume'] +
            bb_signal * self.signal_weights['bb']
        )
        
        # Generate signal based on composite
        if composite > self.composite_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(composite, data),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        elif composite < -self.composite_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(composite, data),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for mixed signals
        elif abs(composite) < 0.3:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': 0.3,
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
        
    def calculate_confidence(self, composite: float, data: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Composite strength
        if abs(composite) > 0.8:
            confidence += 0.3
        elif abs(composite) > 0.6:
            confidence += 0.15
            
        # Signal agreement
        signals = [data.get('rsi_signal', 0), data.get('macd_signal', 0),
                   data.get('ma_signal', 0), data.get('volume_signal', 0),
                   data.get('bb_signal', 0)]
        positive_signals = sum(1 for s in signals if s > 0)
        negative_signals = sum(1 for s in signals if s < 0)
        
        if positive_signals > negative_signals + 2:
            confidence += 0.2
        elif negative_signals > positive_signals + 2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'signal_weights': self.signal_weights,
            'composite_threshold': self.composite_threshold
        }
