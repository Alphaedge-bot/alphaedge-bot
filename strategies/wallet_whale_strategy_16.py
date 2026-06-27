"""
AlphaEdge Strategy – Wallet/Whale Strategy 16
Locked supply and vesting schedule monitoring
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy16:
    """
    Wallet/Whale Strategy 16
    Monitors locked supply and vesting schedules
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_16"
        self.name = "Wallet/Whale Strategy 16"
        self.active = True
        
        # Strategy parameters
        self.locked_supply_threshold = 0.3  # 30%
        self.vesting_activity_threshold = 5
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        locked_supply_pct = data.get('locked_supply_pct', 0)
        vesting_events = data.get('vesting_events', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for high locked supply (buy)
        if locked_supply_pct > self.locked_supply_threshold:
            if vesting_events > self.vesting_activity_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(locked_supply_pct, vesting_events, volume_ratio),
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
        
    def calculate_confidence(self, locked_supply_pct: float, vesting_events: int, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Locked supply
        if locked_supply_pct > 0.5:
            confidence += 0.2
        elif locked_supply_pct > 0.3:
            confidence += 0.1
            
        # Vesting events
        if vesting_events > 10:
            confidence += 0.2
        elif vesting_events > 5:
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
            'locked_supply_threshold': self.locked_supply_threshold
        }
