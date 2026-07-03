"""
AlphaEdge Strategy – Advanced AI/ML Strategy 7
Autoencoder for market microstructure anomaly detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdvancedAIMLStrategy7:
    """
    Advanced AI/ML Strategy 7
    Uses autoencoder for microstructure anomaly detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "advanced_ai_ml_7"
        self.name = "Advanced AI/ML Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.reconstruction_error_threshold = 0.3
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        reconstruction_error = data.get('reconstruction_error', 0)
        anomaly_type = data.get('anomaly_type', 'normal')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for autoencoder anomaly signal
        if reconstruction_error > self.reconstruction_error_threshold:
            if anomaly_type != 'normal':
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'microstructure_anomaly',
                        'confidence': self.calculate_confidence(reconstruction_error, anomaly_type),
                        'reconstruction_error': reconstruction_error,
                        'anomaly_type': anomaly_type,
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
        
    def calculate_confidence(self, reconstruction_error: float, anomaly_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Reconstruction error
        if reconstruction_error > 0.5:
            confidence += 0.2
        elif reconstruction_error > 0.3:
            confidence += 0.1
            
        # Anomaly type
        if anomaly_type in ['critical', 'high']:
            confidence += 0.2
        elif anomaly_type in ['medium']:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'reconstruction_error_threshold': self.reconstruction_error_threshold
        }
