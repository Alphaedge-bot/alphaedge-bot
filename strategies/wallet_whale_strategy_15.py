"""
AlphaEdge Strategy – Wallet/Whale Strategy 15
FOMO (Fear Of Missing Out) detection from wallet activity
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy15:
    """
    Wallet/Whale Strategy 15
    Detects FOMO from wallet activity patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_15"
        self.name = "Wallet/Whale Strategy 15"
        self.active = True
        
        # Strategy parameters
        self.fomo_threshold = 10  # new wallets buying
        self.volume_spike_threshold = 3.0  # 3x normal
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        new_buyers = data.get('new_buyers', 0)
        volume_spike = data.get('volume_spike', 1.0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for FOMO activity
        if new_buyers > self.fomo_threshold:
            if volume_spike > self.volume_spike_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(new_buyers, volume_spike, volume_ratio),
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
        
    def calculate_confidence(self, new_buyers: int, volume_spike: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # New buyers
        if new_buyers > 20:
            confidence += 0.2
        elif new_buyers > 10:
            confidence += 0.1
            
        # Volume spike
        if volume_spike > 5.0:
            confidence += 0.2
        elif volume_spike > 3.0:
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
            'fomo_threshold': self.fomo_threshold
        }
