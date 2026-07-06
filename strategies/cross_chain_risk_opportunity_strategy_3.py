"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 3
Cross-chain bridge liquidity analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy3:
    """
    Cross-Chain Risk & Opportunity Strategy 3
    Analyzes cross-chain bridge liquidity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_3"
        self.name = "Cross-Chain Risk & Opportunity Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.liquidity_threshold = 1000000  # $1M
        self.liquidity_ratio_threshold = 0.3  # 30%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        bridge_liquidity = data.get('bridge_liquidity', 0)
        liquidity_ratio = data.get('liquidity_ratio', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge liquidity signal
        if bridge_liquidity > self.liquidity_threshold:
            if liquidity_ratio > self.liquidity_ratio_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_liquidity_healthy',
                        'confidence': self.calculate_confidence(bridge_liquidity, liquidity_ratio),
                        'bridge_liquidity': bridge_liquidity,
                        'liquidity_ratio': liquidity_ratio,
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
        
    def calculate_confidence(self, bridge_liquidity: float, liquidity_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Bridge liquidity
        if bridge_liquidity > 5000000:
            confidence += 0.2
        elif bridge_liquidity > 1000000:
            confidence += 0.1
            
        # Liquidity ratio
        if liquidity_ratio > 0.5:
            confidence += 0.2
        elif liquidity_ratio > 0.3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'liquidity_threshold': self.liquidity_threshold,
            'liquidity_ratio_threshold': self.liquidity_ratio_threshold
        }
