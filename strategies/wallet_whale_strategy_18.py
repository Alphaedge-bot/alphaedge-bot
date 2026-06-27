"""
AlphaEdge Strategy – Wallet/Whale Strategy 18
Multi-sig wallet activity monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy18:
    """
    Wallet/Whale Strategy 18
    Monitors multi-sig wallet activity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_18"
        self.name = "Wallet/Whale Strategy 18"
        self.active = True
        
        # Strategy parameters
        self.multi_sig_activity_threshold = 3
        self.required_confirmations = 2
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        multi_sig_activity = data.get('multi_sig_activity', [])
        confirmations = data.get('confirmations', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for multi-sig activity
        if len(multi_sig_activity) > self.multi_sig_activity_threshold:
            if confirmations >= self.required_confirmations:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(len(multi_sig_activity), confirmations, volume_ratio),
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
        
    def calculate_confidence(self, activity_count: int, confirmations: int, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Activity count
        if activity_count > 5:
            confidence += 0.2
        elif activity_count > 3:
            confidence += 0.1
            
        # Confirmations
        if confirmations >= 5:
            confidence += 0.2
        elif confirmations >= 2:
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
            'multi_sig_activity_threshold': self.multi_sig_activity_threshold
        }
