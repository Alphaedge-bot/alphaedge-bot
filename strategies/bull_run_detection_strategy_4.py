"""
AlphaEdge Strategy – Bull Run Detection Strategy 4
Social FOMO and euphoria detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class BullRunDetectionStrategy4:
    """
    Bull Run Detection Strategy 4
    Detects social FOMO and euphoria
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "bull_run_detection_4"
        self.name = "Bull Run Detection Strategy 4"
        self.active = True
        
        # Strategy parameters
        self.fomo_threshold = 0.7
        self.social_volume_threshold = 10000
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("social_data_update", self.handle_social_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_social_data(self, event: Event):
        """Handle social data updates"""
        data = event.data
        fomo_score = data.get('fomo_score', 0)
        social_volume = data.get('social_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for FOMO conditions
        if fomo_score > self.fomo_threshold:
            if social_volume > self.social_volume_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'fomo_detected',
                        'confidence': self.calculate_confidence(fomo_score, social_volume),
                        'fomo_score': fomo_score,
                        'social_volume': social_volume,
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
        
    def calculate_confidence(self, fomo_score: float, social_volume: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # FOMO score
        if fomo_score > 0.85:
            confidence += 0.2
        elif fomo_score > 0.7:
            confidence += 0.1
            
        # Social volume
        if social_volume > 50000:
            confidence += 0.2
        elif social_volume > 10000:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'fomo_threshold': self.fomo_threshold,
            'social_volume_threshold': self.social_volume_threshold
        }
