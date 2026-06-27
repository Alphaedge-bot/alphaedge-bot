"""
AlphaEdge Strategy – AI/ML Signals Strategy 2
XGBoost feature importance and signal generation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AIMLSignalsStrategy2:
    """
    AI/ML Signals Strategy 2
    Uses XGBoost feature importance for signal generation
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "ai_ml_signals_2"
        self.name = "AI/ML Signals Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.importance_threshold = 0.1
        self.signal_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        feature_importance = data.get('feature_importance', {})
        xgboost_prediction = data.get('xgboost_prediction', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check if top features are aligned
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
        aligned = sum(1 for _, importance in top_features if importance > self.importance_threshold)
        
        if aligned >= 2 and xgboost_prediction > self.signal_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'buy',
                    'confidence': self.calculate_confidence(aligned, xgboost_prediction),
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
        
    def calculate_confidence(self, aligned: int, prediction: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Feature alignment
        if aligned >= 3:
            confidence += 0.2
        elif aligned >= 2:
            confidence += 0.1
            
        # Prediction strength
        if prediction > 0.8:
            confidence += 0.2
        elif prediction > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'importance_threshold': self.importance_threshold,
            'signal_threshold': self.signal_threshold
        }
