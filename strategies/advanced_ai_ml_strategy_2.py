"""
AlphaEdge Strategy – Advanced AI/ML Strategy 2
XGBoost market regime classification
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedAIMLStrategy2:
    """
    Advanced AI/ML Strategy 2
    Uses XGBoost for market regime classification
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "advanced_ai_ml_2"
        self.name = "Advanced AI/ML Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.classification_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        regime_class = data.get('regime_class', 'neutral')
        regime_confidence = data.get('regime_confidence', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for XGBoost regime signal
        if regime_confidence > self.classification_threshold:
            if volume_ratio > self.volume_confirm:
                # Map regime to trading signal
                if regime_class in ['bull', 'alt_season']:
                    signal_type = 'buy'
                elif regime_class in ['bear', 'crash']:
                    signal_type = 'sell'
                else:
                    signal_type = 'neutral'
                    
                if signal_type != 'neutral':
                    signal = {
                        'strategy': self.strategy_id,
                        'type': signal_type,
                        'confidence': self.calculate_confidence(regime_confidence, regime_class),
                        'regime_class': regime_class,
                        'regime_confidence': regime_confidence,
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
        
    def calculate_confidence(self, regime_confidence: float, regime_class: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Regime confidence
        if regime_confidence > 0.85:
            confidence += 0.2
        elif regime_confidence > 0.7:
            confidence += 0.1
            
        # Regime class
        if regime_class in ['bull', 'alt_season']:
            confidence += 0.2
        elif regime_class in ['bear', 'crash']:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'classification_threshold': self.classification_threshold
        }
