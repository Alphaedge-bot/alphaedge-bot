"""
AlphaEdge Strategy – Wallet/Whale Strategy 8
Fresh wallet creation and suspicious activity detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy8:
    """
    Wallet/Whale Strategy 8
    Detects fresh wallet creation and suspicious activity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_8"
        self.name = "Wallet/Whale Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.new_wallet_threshold = 10
        self.suspicious_activity_threshold = 0.3  # 30% new wallets
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        new_wallets = data.get('new_wallets', 0)
        total_wallets = data.get('total_wallets', 0)
        suspicious_activity = data.get('suspicious_activity', False)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for suspicious activity
        if suspicious_activity and volume_ratio > self.volume_confirm:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': self.calculate_confidence(new_wallets, suspicious_activity, volume_ratio),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for unusual new wallet creation
        if new_wallets > self.new_wallet_threshold:
            if total_wallets > 0:
                new_wallet_pct = new_wallets / total_wallets
                if new_wallet_pct > self.suspicious_activity_threshold:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': 0.6,
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
        
    def calculate_confidence(self, new_wallets: int, suspicious_activity: bool, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # New wallet count
        if new_wallets > 20:
            confidence += 0.2
        elif new_wallets > 10:
            confidence += 0.1
            
        # Suspicious activity
        if suspicious_activity:
            confidence += 0.2
            
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
            'new_wallet_threshold': self.new_wallet_threshold
        }
