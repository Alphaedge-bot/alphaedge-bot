"""
AlphaEdge Strategy – AlphaEdge Proprietary Strategy 2
AlphaEdge Regime Adaptor (ARA)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlphaEdgeProprietaryStrategy2:
    """
    AlphaEdge Proprietary Strategy 2
    AlphaEdge Regime Adaptor - Adapts to market regimes
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "alphaedge_proprietary_2"
        self.name = "AlphaEdge Proprietary Strategy 2"
        self.active = True
        
        # Strategy parameters (Proprietary)
        self.regime_weights = {
            'bull': {'momentum': 0.4, 'breakout': 0.3, 'trend': 0.3},
            'bear': {'defensive': 0.4, 'mean_reversion': 0.3, 'short': 0.3},
            'sideways': {'range': 0.4, 'breakout': 0.3, 'mean_reversion': 0.3},
            'volatile': {'hedge': 0.4, 'options': 0.3, 'scalp': 0.3}
        }
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        current_regime = data.get('regime', 'neutral')
        regime_confidence = data.get('regime_confidence', 0.5)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Get weights for current regime
        if current_regime in self.regime_weights:
            weights = self.regime_weights[current_regime]
            
            # Calculate regime score
            regime_score = 0
            for component, weight in weights.items():
                component_value = data.get(component, 0.5)
                regime_score += component_value * weight
                
            # Check for regime-adapted signal
            if regime_score > 0.6 and regime_confidence > 0.6:
                if volume_ratio > 1.2:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy' if current_regime in ['bull', 'sideways'] else 'sell',
                        'confidence': self.calculate_confidence(regime_score, regime_confidence),
                        'regime': current_regime,
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
        
    def calculate_confidence(self, regime_score: float, confidence: float) -> float:
        """Calculate signal confidence"""
        conf = 0.5
        
        # Regime score
        if regime_score > 0.8:
            conf += 0.2
        elif regime_score > 0.6:
            conf += 0.1
            
        # Confidence
        if confidence > 0.8:
            conf += 0.2
        elif confidence > 0.6:
            conf += 0.1
            
        return min(1.0, max(0, conf))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'regime_weights': self.regime_weights
        }
