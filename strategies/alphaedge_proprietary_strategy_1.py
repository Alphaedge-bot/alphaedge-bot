"""
AlphaEdge Strategy – AlphaEdge Proprietary Strategy 1
AlphaEdge Momentum Composite (AEMC)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlphaEdgeProprietaryStrategy1:
    """
    AlphaEdge Proprietary Strategy 1
    AlphaEdge Momentum Composite (AEMC) - Proprietary momentum scoring
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "alphaedge_proprietary_1"
        self.name = "AlphaEdge Proprietary Strategy 1"
        self.active = True
        
        # Strategy parameters (Proprietary)
        self.momentum_components = {
            'price_momentum': 0.35,
            'volume_momentum': 0.25,
            'relative_strength': 0.20,
            'acceleration': 0.20
        }
        self.momentum_threshold = 0.7
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        price_momentum = data.get('price_momentum', 0)
        volume_momentum = data.get('volume_momentum', 0)
        relative_strength = data.get('relative_strength', 0)
        acceleration = data.get('acceleration', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate AEMC score
        aemc_score = (
            price_momentum * self.momentum_components['price_momentum'] +
            volume_momentum * self.momentum_components['volume_momentum'] +
            relative_strength * self.momentum_components['relative_strength'] +
            acceleration * self.momentum_components['acceleration']
        )
        
        # Check for strong momentum
        if aemc_score > self.momentum_threshold:
            if volume_ratio > 1.2:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(aemc_score),
                    'aemc_score': aemc_score,
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
        
    def calculate_confidence(self, aemc_score: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # AEMC score
        if aemc_score > 0.85:
            confidence += 0.3
        elif aemc_score > 0.7:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'momentum_components': self.momentum_components,
            'momentum_threshold': self.momentum_threshold
        }
