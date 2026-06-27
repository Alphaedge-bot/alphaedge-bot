"""
AlphaEdge Strategy – On-Chain Advanced Strategy 7
Transaction count and network utilization analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OnChainAdvancedStrategy7:
    """
    On-Chain Advanced Strategy 7
    Analyzes transaction count and network utilization
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "onchain_advanced_7"
        self.name = "On-Chain Advanced Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.tx_growth_threshold = 0.03  # 3%
        self.network_utilization_threshold = 0.7  # 70%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        tx_count = data.get('tx_count', 0)
        prev_tx_count = data.get('prev_tx_count', 0)
        network_utilization = data.get('network_utilization', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if prev_tx_count > 0:
            tx_growth = (tx_count - prev_tx_count) / prev_tx_count
            
            # Check for transaction growth (buy)
            if tx_growth > self.tx_growth_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(tx_growth, volume_ratio),
                        'timestamp': datetime.now().isoformat()
                    }
                    signal_event = Event(
                        event_type="signal_generated",
                        data=signal,
                        source=self.strategy_id
                    )
                    await self.event_bus.publish(signal_event)
                    
        # Check for high network utilization (buy)
        if network_utilization > self.network_utilization_threshold:
            if volume_ratio > self.volume_confirm:
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
        
    def calculate_confidence(self, tx_growth: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Transaction growth strength
        if tx_growth > 0.05:
            confidence += 0.3
        elif tx_growth > 0.03:
            confidence += 0.15
            
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.2
        elif volume_ratio > 1.2:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tx_growth_threshold': self.tx_growth_threshold
        }
