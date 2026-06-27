"""
AlphaEdge Strategy – Technical TA Strategy 14
Multi-timeframe analysis and confirmation signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy14:
    """
    Technical TA Strategy 14
    Uses multi-timeframe analysis for signal confirmation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_14"
        self.name = "Technical TA Strategy 14"
        self.active = True
        
        # Strategy parameters
        self.tf_weight = {
            '1m': 0.2,
            '5m': 0.3,
            '15m': 0.5,
            '1h': 0.7,
            '4h': 0.8,
            '1d': 0.9
        }
        self.min_aligned_tfs = 3
        self.alignment_threshold = 0.7
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        tf_signals = data.get('tf_signals', {})
        
        # Calculate alignment score
        alignment_score = self.calculate_alignment(tf_signals)
        
        # Check for strong alignment (bullish)
        if alignment_score > self.alignment_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(alignment_score, tf_signals),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for strong alignment (bearish)
        elif alignment_score < -self.alignment_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(alignment_score, tf_signals),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for mixed signals
        elif abs(alignment_score) < 0.3:
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
        
    def calculate_alignment(self, tf_signals: Dict) -> float:
        """Calculate alignment score across timeframes"""
        if not tf_signals:
            return 0
            
        weighted_score = 0
        total_weight = 0
        
        for tf, signal in tf_signals.items():
            weight = self.tf_weight.get(tf, 0.5)
            weighted_score += signal * weight
            total_weight += weight
            
        if total_weight == 0:
            return 0
            
        return weighted_score / total_weight
        
    def calculate_confidence(self, alignment_score: float, tf_signals: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Alignment strength
        if abs(alignment_score) > 0.8:
            confidence += 0.3
        elif abs(alignment_score) > 0.6:
            confidence += 0.15
            
        # Number of aligned timeframes
        aligned_tfs = sum(1 for s in tf_signals.values() if abs(s) > 0.3)
        if aligned_tfs >= 4:
            confidence += 0.2
        elif aligned_tfs >= 3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'min_aligned_tfs': self.min_aligned_tfs
        }
