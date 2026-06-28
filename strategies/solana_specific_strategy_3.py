"""
AlphaEdge Strategy – Solana Specific Strategy 3
Solana NFT ecosystem analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SolanaSpecificStrategy3:
    """
    Solana Specific Strategy 3
    Analyzes Solana NFT ecosystem
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "solana_specific_3"
        self.name = "Solana Specific Strategy 3"
        self.active = True
        
        # Strategy parameters
        self.nft_volume_threshold = 1000000  # $1M
        self.nft_collection_count_threshold = 100
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        nft_volume = data.get('solana_nft_volume', 0)
        nft_collections = data.get('solana_nft_collections', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for NFT ecosystem signal
        if nft_volume > self.nft_volume_threshold:
            if nft_collections > self.nft_collection_count_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'nft_ecosystem',
                        'confidence': self.calculate_confidence(nft_volume, nft_collections),
                        'nft_volume': nft_volume,
                        'nft_collections': nft_collections,
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
        
    def calculate_confidence(self, nft_volume: float, nft_collections: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # NFT volume
        if nft_volume > 5000000:
            confidence += 0.2
        elif nft_volume > 1000000:
            confidence += 0.1
            
        # NFT collections
        if nft_collections > 200:
            confidence += 0.2
        elif nft_collections > 100:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'nft_volume_threshold': self.nft_volume_threshold,
            'nft_collection_count_threshold': self.nft_collection_count_threshold
        }
