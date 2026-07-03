"""
AlphaEdge Strategy – Quantum Inspired Strategy 2
Quantum superposition for multi-state market analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class QuantumInspiredStrategy2:
    """
    Quantum Inspired Strategy 2
    Uses quantum superposition for multi-state market analysis
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "quantum_inspired_2"
        self.name = "Quantum Inspired Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.superposition_threshold = 0.6
        self.probability_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        superposition_score = data.get('superposition_score', 0)
        probability_distribution = data.get('probability_distribution', {})
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for superposition signal
        if superposition_score > self.superposition_threshold:
            if probability_distribution:
                # Find highest probability state
                best_state = max(probability_distribution, key=probability_distribution.get)
                best_probability = probability_distribution[best_state]
                
                if best_probability > self.probability_threshold:
                    if volume_ratio > self.volume_confirm:
                        # Map state to direction
                        direction = 'buy' if best_state in ['bull', 'up'] else 'sell' if best_state in ['bear', 'down'] else 'neutral'
                        
                        if direction != 'neutral':
                            signal = {
                                'strategy': self.strategy_id,
                                'type': direction,
                                'confidence': self.calculate_confidence(superposition_score, best_probability),
                                'superposition_score': superposition_score,
                                'best_state': best_state,
                                'best_probability': best_probability,
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
        
    def calculate_confidence(self, superposition_score: float, best_probability: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Superposition score
        if superposition_score > 0.8:
            confidence += 0.2
        elif superposition_score > 0.6:
            confidence += 0.1
            
        # Best probability
        if best_probability > 0.85:
            confidence += 0.2
        elif best_probability > 0.7:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'superposition_threshold': self.superposition_threshold,
            'probability_threshold': self.probability_threshold
        }
