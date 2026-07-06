"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 5
Cross-chain bridge exploit detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy5:
    """
    Cross-Chain Risk & Opportunity Strategy 5
    Detects cross-chain bridge exploits
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_5"
        self.name = "Cross-Chain Risk & Opportunity Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.exploit_risk_threshold = 0.5
        self.anomaly_threshold = 0.7
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        exploit_risk = data.get('exploit_risk', 0)
        anomaly_score = data.get('anomaly_score', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for exploit detection signal
        if exploit_risk > self.exploit_risk_threshold:
            if anomaly_score > self.anomaly_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_exploit_detected',
                        'confidence': self.calculate_confidence(exploit_risk, anomaly_score),
                        'exploit_risk': exploit_risk,
                        'anomaly_score': anomaly_score,
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
        
    def calculate_confidence(self, exploit_risk: float, anomaly_score: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Exploit risk
        if exploit_risk > 0.7:
            confidence += 0.2
        elif exploit_risk > 0.5:
            confidence += 0.1
            
        # Anomaly score
        if anomaly_score > 0.85:
            confidence += 0.2
        elif anomaly_score > 0.7:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'exploit_risk_threshold': self.exploit_risk_threshold,
            'anomaly_threshold': self.anomaly_threshold
        }
