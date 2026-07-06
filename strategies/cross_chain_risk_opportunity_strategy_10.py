"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 10
Cross-chain bridge latency and speed analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy10:
    """
    Cross-Chain Risk & Opportunity Strategy 10
    Analyzes cross-chain bridge latency and speed
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_10"
        self.name = "Cross-Chain Risk & Opportunity Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.latency_threshold = 60  # seconds
        self.speed_score_threshold = 0.6
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_latency = data.get('bridge_latency', 0)
        speed_score = data.get('speed_score', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge latency signal
        if bridge_latency < self.latency_threshold:
            if speed_score > self.speed_score_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_fast',
                        'confidence': self.calculate_confidence(bridge_latency, speed_score),
                        'bridge_latency': bridge_latency,
                        'speed_score': speed_score,
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
        
    def calculate_confidence(self, bridge_latency: float, speed_score: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Bridge latency
        if bridge_latency < 30:
            confidence += 0.2
        elif bridge_latency < 60:
            confidence += 0.1
            
        # Speed score
        if speed_score > 0.8:
            confidence += 0.2
        elif speed_score > 0.6:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'latency_threshold': self.latency_threshold,
            'speed_score_threshold': self.speed_score_threshold
        }
