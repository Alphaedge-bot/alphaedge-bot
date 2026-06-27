"""
AlphaEdge Strategy – Wallet/Whale Strategy 17
Gas fee analysis for network activity detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy17:
    """
    Wallet/Whale Strategy 17
    Analyzes gas fees for network activity detection
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_17"
        self.name = "Wallet/Whale Strategy 17"
        self.active = True
        
        # Strategy parameters
        self.gas_spike_threshold = 2.0  # 2x normal
        self.gas_volume_threshold = 1000
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        gas_price = data.get('gas_price', 0)
        avg_gas_price = data.get('avg_gas_price', 1)
        gas_volume = data.get('gas_volume', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if avg_gas_price > 0:
            gas_spike = gas_price / avg_gas_price
            
            # Check for gas spike (network activity)
            if gas_spike > self.gas_spike_threshold:
                if gas_volume > self.gas_volume_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'buy',
                            'confidence': self.calculate_confidence(gas_spike, gas_volume, volume_ratio),
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
        
    def calculate_confidence(self, gas_spike: float, gas_volume: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Gas spike
        if gas_spike > 3.0:
            confidence += 0.2
        elif gas_spike > 2.0:
            confidence += 0.1
            
        # Gas volume
        if gas_volume > 5000:
            confidence += 0.2
        elif gas_volume > 1000:
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
            'gas_spike_threshold': self.gas_spike_threshold
        }
