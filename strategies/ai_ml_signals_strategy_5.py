"""
AlphaEdge Strategy – AI/ML Signals Strategy 5
Ensemble AI model consensus and signal fusion
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AIMLSignalsStrategy5:
    """
    AI/ML Signals Strategy 5
    Uses ensemble AI model consensus for signal fusion
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ai_ml_signals_5"
        self.name = "AI/ML Signals Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.consensus_threshold = 0.7
        self.min_models = 3
        self.weights = {
            'lstm': 0.30,
            'xgboost': 0.25,
            'transformer': 0.25,
            'reinforcement': 0.20
        }
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        model_predictions = data.get('model_predictions', {})
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate weighted consensus
        consensus = 0
        total_weight = 0
        model_count = 0
        
        for model, prediction in model_predictions.items():
            weight = self.weights.get(model, 0)
            if weight > 0:
                consensus += prediction * weight
                total_weight += weight
                model_count += 1
        
        if total_weight > 0:
            consensus /= total_weight
            
            # Check for strong consensus
            if consensus > self.consensus_threshold and model_count >= self.min_models:
                if volume_ratio > 1.2:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(consensus, model_count),
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
        
    def calculate_confidence(self, consensus: float, model_count: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Consensus strength
        if consensus > 0.85:
            confidence += 0.2
        elif consensus > 0.7:
            confidence += 0.1
            
        # Model count
        if model_count >= 4:
            confidence += 0.2
        elif model_count >= 3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'consensus_threshold': self.consensus_threshold,
            'min_models': self.min_models,
            'weights': self.weights
        }
