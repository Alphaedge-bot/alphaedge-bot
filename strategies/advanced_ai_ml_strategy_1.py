"""
AlphaEdge Strategy – Advanced AI/ML Strategy 1
Deep Learning price prediction with LSTM
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedAIMLStrategy1:
    """
    Advanced AI/ML Strategy 1
    Uses LSTM for deep learning price prediction
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "advanced_ai_ml_1"
        self.name = "Advanced AI/ML Strategy 1"
        self.active = True
        
        # Strategy parameters
        self.prediction_threshold = 0.03  # 3%
        self.confidence_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        lstm_prediction = data.get('lstm_prediction', 0)
        lstm_confidence = data.get('lstm_confidence', 0.5)
        current_price = data.get('price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if current_price > 0:
            predicted_change = (lstm_prediction - current_price) / current_price
            
            # Check for LSTM signal
            if abs(predicted_change) > self.prediction_threshold:
                if lstm_confidence > self.confidence_threshold:
                    if volume_ratio > self.volume_confirm:
                        direction = 'buy' if predicted_change > 0 else 'sell'
                        signal = {
                            'strategy': self.strategy_id,
                            'type': direction,
                            'confidence': self.calculate_confidence(predicted_change, lstm_confidence),
                            'predicted_change': predicted_change,
                            'lstm_confidence': lstm_confidence,
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
        
    def calculate_confidence(self, predicted_change: float, lstm_confidence: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Predicted change
        if abs(predicted_change) > 0.05:
            confidence += 0.2
        elif abs(predicted_change) > 0.03:
            confidence += 0.1
            
        # LSTM confidence
        if lstm_confidence > 0.85:
            confidence += 0.2
        elif lstm_confidence > 0.7:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'prediction_threshold': self.prediction_threshold,
            'confidence_threshold': self.confidence_threshold
        }
