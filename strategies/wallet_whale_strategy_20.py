"""
AlphaEdge Strategy – Wallet/Whale Strategy 20
NFT and token-gated community activity monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy20:
    """
    Wallet/Whale Strategy 20
    Monitors NFT and token-gated community activity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_20"
        self.name = "Wallet/Whale Strategy 20"
        self.active = True
        
        # Strategy parameters
        self.nft_activity_threshold = 5
        self.token_gated_threshold = 10
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        nft_activity = data.get('nft_activity', [])
        token_gated_members = data.get('token_gated_members', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for NFT/token-gated activity
        if len(nft_activity) > self.nft_activity_threshold:
            if token_gated_members > self.token_gated_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(len(nft_activity), token_gated_members, volume_ratio),
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
        
    def calculate_confidence(self, nft_activity: int, token_gated_members: int, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # NFT activity
        if nft_activity > 10:
            confidence += 0.2
        elif nft_activity > 5:
            confidence += 0.1
            
        # Token-gated members
        if token_gated_members > 20:
            confidence += 0.2
        elif token_gated_members > 10:
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
            'nft_activity_threshold': self.nft_activity_threshold
        }
