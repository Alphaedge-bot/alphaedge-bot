"""
AlphaEdge Strategy – AlphaEdge Proprietary Strategy 9
AlphaEdge Breakout Confidence (ABC)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlphaEdgeProprietaryStrategy9:
    """
    AlphaEdge Proprietary Strategy 9
    AlphaEdge Breakout Confidence - Proprietary breakout confidence scoring
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "alphaedge_proprietary_9"
        self.name = "AlphaEdge Proprietary Strategy 9"
        self.active = True
        
        # Strategy parameters (Proprietary)
        self.breakout_confidence_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        breakout_confidence = data.get('breakout_confidence', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high breakout confidence
        if breakout_confidence > self.breakout_confidence_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(breakout_confidence),
                    'breakout_confidence': breakout_confidence,
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
        
    def calculate_confidence(self, breakout_confidence: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Breakout confidence
        if breakout_confidence > 0.85:
            confidence += 0.3
        elif breakout_confidence > 0.7:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'breakout_confidence_threshold': self.breakout_confidence_threshold
        }
