"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 13
Cross-chain bridge fee comparison and optimization
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy13:
    """
    Cross-Chain Risk & Opportunity Strategy 13
    Compares and optimizes cross-chain bridge fees
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_13"
        self.name = "Cross-Chain Risk & Opportunity Strategy 13"
        self.active = True
        
        # Strategy parameters
        self.fee_optimization_threshold = 0.3  # 30% savings
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        fee_savings = data.get('fee_savings', 0)
        best_bridge = data.get('best_bridge', '')
        current_bridge = data.get('current_bridge', '')
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for fee optimization signal
        if fee_savings > self.fee_optimization_threshold:
            if best_bridge and current_bridge:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_optimization',
                        'confidence': self.calculate_confidence(fee_savings),
                        'fee_savings': fee_savings,
                        'best_bridge': best_bridge,
                        'current_bridge': current_bridge,
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
        
    def calculate_confidence(self, fee_savings: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Fee savings
        if fee_savings > 0.5:
            confidence += 0.3
        elif fee_savings > 0.3:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'fee_optimization_threshold': self.fee_optimization_threshold
        }
