"""
AlphaEdge Strategy – Wallet/Whale Strategy 14
Cross-chain wallet movement tracking
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy14:
    """
    Wallet/Whale Strategy 14
    Tracks cross-chain wallet movements
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_14"
        self.name = "Wallet/Whale Strategy 14"
        self.active = True
        
        # Strategy parameters
        self.cross_chain_threshold = 10000  # tokens
        self.bridge_activity_threshold = 5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        cross_chain_movements = data.get('cross_chain_movements', [])
        bridge_activity = data.get('bridge_activity', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for cross-chain activity
        if cross_chain_movements:
            total_movement = sum(m.get('amount', 0) for m in cross_chain_movements)
            if total_movement > self.cross_chain_threshold:
                if bridge_activity > self.bridge_activity_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'buy',
                            'confidence': self.calculate_confidence(total_movement, bridge_activity, volume_ratio),
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
        
    def calculate_confidence(self, total_movement: float, bridge_activity: int, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Cross-chain movement
        if total_movement > 50000:
            confidence += 0.2
        elif total_movement > 10000:
            confidence += 0.1
            
        # Bridge activity
        if bridge_activity > 10:
            confidence += 0.2
        elif bridge_activity > 5:
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
            'cross_chain_threshold': self.cross_chain_threshold
        }
