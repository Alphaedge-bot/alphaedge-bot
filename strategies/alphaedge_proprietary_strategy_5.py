"""
AlphaEdge Strategy – AlphaEdge Proprietary Strategy 5
AlphaEdge Whale Detector (AWD)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlphaEdgeProprietaryStrategy5:
    """
    AlphaEdge Proprietary Strategy 5
    AlphaEdge Whale Detector - Proprietary whale activity detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "alphaedge_proprietary_5"
        self.name = "AlphaEdge Proprietary Strategy 5"
        self.active = True
        
        # Strategy parameters (Proprietary)
        self.whale_threshold = 1000000
        self.whale_signal_threshold = 0.7
        self.whale_tracking_window = 10
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        whale_transactions = data.get('whale_transactions', [])
        whale_confidence = data.get('whale_confidence', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Analyze whale activity
        whale_count = len([t for t in whale_transactions if t.get('value', 0) > self.whale_threshold])
        whale_score = min(1, whale_count / self.whale_tracking_window)
        
        # Check for whale accumulation signal
        if whale_score > self.whale_signal_threshold:
            if whale_confidence > 0.6:
                if volume_ratio > 1.2:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(whale_score, whale_confidence),
                        'whale_score': whale_score,
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
        
    def calculate_confidence(self, whale_score: float, whale_confidence: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Whale score
        if whale_score > 0.9:
            confidence += 0.2
        elif whale_score > 0.7:
            confidence += 0.1
            
        # Whale confidence
        if whale_confidence > 0.8:
            confidence += 0.2
        elif whale_confidence > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'whale_threshold': self.whale_threshold,
            'whale_signal_threshold': self.whale_signal_threshold
        }
