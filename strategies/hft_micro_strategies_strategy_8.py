"""
AlphaEdge Strategy – HFT Micro Strategy 8
Micro-order flow imbalance and reversal detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class HFTMicroStrategiesStrategy8:
    """
    HFT Micro Strategy 8
    Detects micro-order flow imbalance and reversals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "hft_micro_strategies_8"
        self.name = "HFT Micro Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.flow_imbalance_threshold = 0.3
        self.reversal_threshold = 0.5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        flow_imbalance = data.get('flow_imbalance', 0)
        reversal_probability = data.get('reversal_probability', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for flow imbalance signal
        if abs(flow_imbalance) > self.flow_imbalance_threshold:
            if reversal_probability > self.reversal_threshold:
                if volume_ratio > self.volume_confirm:
                    direction = 'buy' if flow_imbalance > 0 else 'sell'
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'flow_reversal',
                        'confidence': self.calculate_confidence(flow_imbalance, reversal_probability),
                        'flow_imbalance': flow_imbalance,
                        'reversal_probability': reversal_probability,
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
        
    def calculate_confidence(self, flow_imbalance: float, reversal_probability: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Flow imbalance
        if abs(flow_imbalance) > 0.5:
            confidence += 0.2
        elif abs(flow_imbalance) > 0.3:
            confidence += 0.1
            
        # Reversal probability
        if reversal_probability > 0.7:
            confidence += 0.2
        elif reversal_probability > 0.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'flow_imbalance_threshold': self.flow_imbalance_threshold,
            'reversal_threshold': self.reversal_threshold
        }
