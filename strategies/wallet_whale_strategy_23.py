"""
AlphaEdge Strategy – Wallet/Whale Strategy 23
Comprehensive on-chain health score composite
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WalletWhaleStrategy23:
    """
    Wallet/Whale Strategy 23
    Uses comprehensive on-chain health score composite
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "wallet_whale_23"
        self.name = "Wallet/Whale Strategy 23"
        self.active = True
        
        # Strategy parameters
        self.composite_threshold = 0.7
        self.weights = {
            'whale_activity': 0.25,
            'exchange_flow': 0.20,
            'holder_distribution': 0.20,
            'network_activity': 0.20,
            'defi_participation': 0.15
        }
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("onchain_data_update", self.handle_onchain_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_onchain_data(self, event: Event):
        """Handle on-chain data updates"""
        data = event.data
        whale_activity = data.get('whale_activity', 0.5)
        exchange_flow = data.get('exchange_flow', 0.5)
        holder_distribution = data.get('holder_distribution', 0.5)
        network_activity = data.get('network_activity', 0.5)
        defi_participation = data.get('defi_participation', 0.5)
        
        # Calculate composite score
        composite = (
            whale_activity * self.weights['whale_activity'] +
            exchange_flow * self.weights['exchange_flow'] +
            holder_distribution * self.weights['holder_distribution'] +
            network_activity * self.weights['network_activity'] +
            defi_participation * self.weights['defi_participation']
        )
        
        # Generate signal based on composite
        if composite > self.composite_threshold:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(composite, data),
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
        
    def calculate_confidence(self, composite: float, data: Dict) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Composite strength
        if composite > 0.85:
            confidence += 0.3
        elif composite > 0.7:
            confidence += 0.15
            
        # Component alignment
        components = [data.get(k, 0.5) for k in self.weights.keys()]
        positive = sum(1 for c in components if c > 0.6)
        if positive >= 4:
            confidence += 0.2
        elif positive >= 3:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'weights': self.weights,
            'composite_threshold': self.composite_threshold
        }
