"""
AlphaEdge Strategy – Advanced AI/ML Strategy 6
Neural network pattern recognition for market cycles
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedAIMLStrategy6:
    """
    Advanced AI/ML Strategy 6
    Uses neural network for pattern recognition
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "advanced_ai_ml_6"
        self.name = "Advanced AI/ML Strategy 6"
        self.active = True
        
        # Strategy parameters
        self.pattern_confidence_threshold = 0.7
        self.cycle_phase_threshold = 0.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        pattern_confidence = data.get('pattern_confidence', 0)
        cycle_phase = data.get('cycle_phase', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for pattern recognition signal
        if pattern_confidence > self.pattern_confidence_threshold:
            if volume_ratio > self.volume_confirm:
                # Determine signal based on cycle phase
                if cycle_phase < self.cycle_phase_threshold:
                    direction = 'buy'
                else:
                    direction = 'sell'
                    
                signal = {
                    'strategy': self.strategy_id,
                    'type': direction,
                    'confidence': self.calculate_confidence(pattern_confidence, cycle_phase),
                    'pattern_confidence': pattern_confidence,
                    'cycle_phase': cycle_phase,
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
        
    def calculate_confidence(self, pattern_confidence: float, cycle_phase: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Pattern confidence
        if pattern_confidence > 0.85:
            confidence += 0.2
        elif pattern_confidence > 0.7:
            confidence += 0.1
            
        # Cycle phase
        if abs(cycle_phase - 0.5) > 0.3:
            confidence += 0.2
        elif abs(cycle_phase - 0.5) > 0.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'pattern_confidence_threshold': self.pattern_confidence_threshold,
            'cycle_phase_threshold': self.cycle_phase_threshold
        }
