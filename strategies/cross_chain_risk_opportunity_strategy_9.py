"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 9
Cross-chain bridge validator analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy9:
    """
    Cross-Chain Risk & Opportunity Strategy 9
    Analyzes cross-chain bridge validators
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_9"
        self.name = "Cross-Chain Risk & Opportunity Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.validator_count_threshold = 10
        self.stake_distribution_threshold = 0.3  # 30% concentration
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        validator_count = data.get('validator_count', 0)
        stake_distribution = data.get('stake_distribution', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for bridge validator signal
        if validator_count > self.validator_count_threshold:
            if stake_distribution < self.stake_distribution_threshold:  # Lower concentration = better
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'bridge_validators_healthy',
                        'confidence': self.calculate_confidence(validator_count, stake_distribution),
                        'validator_count': validator_count,
                        'stake_distribution': stake_distribution,
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
        
    def calculate_confidence(self, validator_count: int, stake_distribution: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Validator count
        if validator_count > 20:
            confidence += 0.2
        elif validator_count > 10:
            confidence += 0.1
            
        # Stake distribution (lower = better)
        if stake_distribution < 0.15:
            confidence += 0.2
        elif stake_distribution < 0.3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'validator_count_threshold': self.validator_count_threshold,
            'stake_distribution_threshold': self.stake_distribution_threshold
        }
