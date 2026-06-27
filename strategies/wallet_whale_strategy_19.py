"""
AlphaEdge Strategy – Wallet/Whale Strategy 19
Unusual token movement and whale dumping detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy19:
    """
    Wallet/Whale Strategy 19
    Detects unusual token movement and whale dumping
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_19"
        self.name = "Wallet/Whale Strategy 19"
        self.active = True
        
        # Strategy parameters
        self.dump_threshold = 100000  # $100K
        self.unusual_movement_threshold = 5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        large_transfers = data.get('large_transfers', [])
        unusual_movements = data.get('unusual_movements', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for dumping activity
        dump_count = 0
        for transfer in large_transfers:
            if transfer.get('value', 0) > self.dump_threshold:
                dump_count += 1
                
        if dump_count > self.unusual_movement_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'sell',
                    'confidence': self.calculate_confidence(dump_count, unusual_movements, volume_ratio),
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
        
    def calculate_confidence(self, dump_count: int, unusual_movements: int, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Dump count
        if dump_count > 10:
            confidence += 0.2
        elif dump_count > 5:
            confidence += 0.1
            
        # Unusual movements
        if unusual_movements > 10:
            confidence += 0.2
        elif unusual_movements > 5:
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
            'dump_threshold': self.dump_threshold
        }
