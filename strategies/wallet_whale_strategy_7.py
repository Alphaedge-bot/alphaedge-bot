"""
AlphaEdge Strategy – Wallet/Whale Strategy 7
Token distribution and holder count analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy7:
    """
    Wallet/Whale Strategy 7
    Analyzes token distribution and holder counts
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_7"
        self.name = "Wallet/Whale Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.holder_growth_threshold = 0.02  # 2%
        self.distribution_threshold = 0.1    # 10% top holders
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        holder_count = data.get('holder_count', 0)
        prev_holder_count = data.get('prev_holder_count', 0)
        top_holder_pct = data.get('top_holder_pct', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_holder_count > 0:
            holder_growth = (holder_count - prev_holder_count) / prev_holder_count
            
            # Check for healthy distribution (buy)
            if holder_growth > self.holder_growth_threshold and top_holder_pct < self.distribution_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(holder_growth, top_holder_pct, volume_ratio),
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
        
    def calculate_confidence(self, holder_growth: float, top_holder_pct: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Holder growth
        if holder_growth > 0.05:
            confidence += 0.2
        elif holder_growth > 0.02:
            confidence += 0.1
            
        # Distribution
        if top_holder_pct < 0.05:
            confidence += 0.2
        elif top_holder_pct < 0.1:
            confidence += 0.1
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'holder_growth_threshold': self.holder_growth_threshold
        }
