"""
AlphaEdge Strategy – Infrastructure Strategy 2
Scalability and performance metric analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class InfrastructureStrategy2:
    """
    Infrastructure Strategy 2
    Analyzes scalability and performance metrics
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "infrastructure_2"
        self.name = "Infrastructure Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.tps_growth_threshold = 0.05  # 5%
        self.latency_improvement_threshold = 0.1  # 10%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("infrastructure_data_update", self.handle_infrastructure_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_infrastructure_data(self, event: Event):
        """Handle infrastructure data updates"""
        data = event.data
        tps_growth = data.get('tps_growth', 0)
        latency_improvement = data.get('latency_improvement', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for performance improvements
        if tps_growth > self.tps_growth_threshold:
            if latency_improvement > self.latency_improvement_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(tps_growth, latency_improvement),
                        'tps_growth': tps_growth,
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
        
    def calculate_confidence(self, tps_growth: float, latency_improvement: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # TPS growth
        if tps_growth > 0.1:
            confidence += 0.2
        elif tps_growth > 0.05:
            confidence += 0.1
            
        # Latency improvement
        if latency_improvement > 0.2:
            confidence += 0.2
        elif latency_improvement > 0.1:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tps_growth_threshold': self.tps_growth_threshold,
            'latency_improvement_threshold': self.latency_improvement_threshold
        }
