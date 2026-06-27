"""
AlphaEdge Strategy – On-Chain Advanced Strategy 19
Exchange deposit/withdrawal pattern analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OnChainAdvancedStrategy19:
    """
    On-Chain Advanced Strategy 19
    Analyzes exchange deposit/withdrawal patterns
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "onchain_advanced_19"
        self.name = "On-Chain Advanced Strategy 19"
        self.active = True
        
        # Strategy parameters
        self.deposit_threshold = 1000  # tokens
        self.withdrawal_threshold = 1000  # tokens
        self.net_flow_threshold = 0.1  # 10%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        total_deposits = data.get('total_deposits', 0)
        total_withdrawals = data.get('total_withdrawals', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Calculate net flow
        net_flow = total_withdrawals - total_deposits
        total_flow = total_deposits + total_withdrawals
        
        if total_flow > 0:
            net_flow_pct = net_flow / total_flow
            
            # Check for net withdrawal (accumulation)
            if net_flow > self.withdrawal_threshold:
                if net_flow_pct > self.net_flow_threshold:
                    if volume_ratio > self.volume_confirm:
                        signal = {
                            'strategy': self.strategy_id,
                            'type': 'buy',
                            'confidence': self.calculate_confidence(net_flow, volume_ratio),
                            'timestamp': datetime.now().isoformat()
                        }
                        signal_event = Event(
                            event_type="signal_generated",
                            data=signal,
                            source=self.strategy_id
                        )
                        await self.event_bus.publish(signal_event)
                        
        # Check for net deposit (distribution)
        if net_flow < -self.deposit_threshold:
            if net_flow_pct < -self.net_flow_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'sell',
                        'confidence': self.calculate_confidence(net_flow, volume_ratio),
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
        
    def calculate_confidence(self, net_flow: float, volume_ratio: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Net flow strength
        if abs(net_flow) > 5000:
            confidence += 0.3
        elif abs(net_flow) > 1000:
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
            'deposit_threshold': self.deposit_threshold,
            'withdrawal_threshold': self.withdrawal_threshold
        }
