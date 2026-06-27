"""
AlphaEdge Strategy – Wallet/Whale Strategy 21
Airdrop and token distribution event monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy21:
    """
    Wallet/Whale Strategy 21
    Monitors airdrop and token distribution events
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_21"
        self.name = "Wallet/Whale Strategy 21"
        self.active = True
        
        # Strategy parameters
        self.airdrop_threshold = 1000  # recipients
        self.distribution_amount_threshold = 10000  # tokens
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        airdrop_recipients = data.get('airdrop_recipients', 0)
        distribution_amount = data.get('distribution_amount', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for airdrop activity
        if airdrop_recipients > self.airdrop_threshold:
            if distribution_amount > self.distribution_amount_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(airdrop_recipients, distribution_amount, volume_ratio),
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
        
    def calculate_confidence(self, airdrop_recipients: int, distribution_amount: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Airdrop recipients
        if airdrop_recipients > 5000:
            confidence += 0.2
        elif airdrop_recipients > 1000:
            confidence += 0.1
            
        # Distribution amount
        if distribution_amount > 100000:
            confidence += 0.2
        elif distribution_amount > 10000:
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
            'airdrop_threshold': self.airdrop_threshold
        }
