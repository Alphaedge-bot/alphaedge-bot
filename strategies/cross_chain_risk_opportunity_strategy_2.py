"""
AlphaEdge Strategy – Cross-Chain Risk & Opportunity Strategy 2
Cross-chain arbitrage opportunity detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CrossChainRiskOpportunityStrategy2:
    """
    Cross-Chain Risk & Opportunity Strategy 2
    Detects cross-chain arbitrage opportunities
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "cross_chain_risk_opportunity_2"
        self.name = "Cross-Chain Risk & Opportunity Strategy 2"
        self.active = True
        
        # Strategy parameters
        self.arbitrage_threshold = 0.02  # 2% profit
        self.volume_threshold = 100000  # $100K
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        arbitrage_opportunity = data.get('arbitrage_opportunity', {})
        max_profit = data.get('max_profit', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for arbitrage opportunity
        if max_profit > self.arbitrage_threshold:
            if arbitrage_opportunity:
                if volume_ratio > self.volume_confirm:
                    # Extract opportunity details
                    from_chain = arbitrage_opportunity.get('from_chain', 'unknown')
                    to_chain = arbitrage_opportunity.get('to_chain', 'unknown')
                    profit_pct = arbitrage_opportunity.get('profit_pct', 0)
                    
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'arbitrage_opportunity',
                        'confidence': self.calculate_confidence(max_profit, profit_pct),
                        'from_chain': from_chain,
                        'to_chain': to_chain,
                        'profit_pct': profit_pct,
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
        
    def calculate_confidence(self, max_profit: float, profit_pct: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Max profit
        if max_profit > 0.05:
            confidence += 0.2
        elif max_profit > 0.02:
            confidence += 0.1
            
        # Profit percentage
        if profit_pct > 0.03:
            confidence += 0.2
        elif profit_pct > 0.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'arbitrage_threshold': self.arbitrage_threshold,
            'volume_threshold': self.volume_threshold
        }
