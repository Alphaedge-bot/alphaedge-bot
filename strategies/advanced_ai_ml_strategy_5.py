"""
AlphaEdge Strategy – Advanced AI/ML Strategy 5
Ensemble AI model consensus for market prediction
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedAIMLStrategy5:
    """
    Advanced AI/ML Strategy 5
    Uses ensemble AI model consensus for market prediction
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "advanced_ai_ml_5"
        self.name = "Advanced AI/ML Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.consensus_threshold = 0.7
        self.min_models = 3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        model_predictions = data.get('model_predictions', {})
        consensus_score = data.get('consensus_score', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Count active models
        active_models = sum(1 for v in model_predictions.values() if v > 0)
        
        # Check for ensemble consensus signal
        if consensus_score > self.consensus_threshold:
            if active_models >= self.min_models:
                if volume_ratio > self.volume_confirm:
                    direction = 'buy' if consensus_score > 0 else 'sell'
                    signal = {
                        'strategy': self.strategy_id,
                        'type': direction,
                        'confidence': self.calculate_confidence(consensus_score, active_models),
                        'consensus_score': consensus_score,
                        'active_models': active_models,
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
        
    def calculate_confidence(self, consensus_score: float, active_models: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Consensus score
        if abs(consensus_score) > 0.85:
            confidence += 0.2
        elif abs(consensus_score) > 0.7:
            confidence += 0.1
            
        # Active models
        if active_models >= 5:
            confidence += 0.2
        elif active_models >= 3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'consensus_threshold': self.consensus_threshold,
            'min_models': self.min_models
        }
