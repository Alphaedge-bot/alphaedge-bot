"""
AlphaEdge Strategy – Momentum Breakout Strategy 5
Multi-timeframe momentum confirmation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MomentumBreakoutStrategy5:
    """
    Momentum Breakout Strategy 5
    Uses multi-timeframe momentum confirmation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "momentum_breakout_5"
        self.name = "Momentum Breakout Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.tf_weights = {
            '1m': 0.2,
            '5m': 0.3,
            '15m': 0.5,
            '1h': 0.7,
            '4h': 0.8
        }
        self.confirmation_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        tf_momentum = data.get('tf_momentum', {})
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate weighted momentum score
        weighted_momentum = 0
        total_weight = 0
        
        for tf, momentum in tf_momentum.items():
            weight = self.tf_weights.get(tf, 0.5)
            weighted_momentum += momentum * weight
            total_weight += weight
            
        if total_weight > 0:
            momentum_score = weighted_momentum / total_weight
            
            # Check for multi-timeframe confirmation
            if momentum_score > self.confirmation_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'multi_tf_breakout',
                        'confidence': self.calculate_confidence(momentum_score, tf_momentum),
                        'momentum_score': momentum_score,
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
        
    def calculate_confidence(self, momentum_score: float, tf_momentum: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Momentum score
        if momentum_score > 0.8:
            confidence += 0.2
        elif momentum_score > 0.6:
            confidence += 0.1
            
        # Timeframe alignment
        aligned_tfs = sum(1 for m in tf_momentum.values() if m > 0.5)
        total_tfs = len(tf_momentum)
        if total_tfs > 0:
            alignment = aligned_tfs / total_tfs
            if alignment > 0.7:
                confidence += 0.2
            elif alignment > 0.5:
                confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tf_weights': self.tf_weights,
            'confirmation_threshold': self.confirmation_threshold
        }
