"""
AlphaEdge Strategy – Crypto Macro Strategy 17
Monitors crypto mining and network activity for signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy17:
    """
    Crypto Macro Strategy 17
    Uses mining and network activity to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_17"
        self.name = "Crypto Macro Strategy 17"
        self.active = True
        
        # Strategy parameters
        self.hashrate_threshold = 500000000  # 500 EH/s
        self.mining_difficulty_threshold = 50
        self.network_activity_threshold = 1000000  # 1M transactions
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        hashrate = data.get('hashrate', 0)
        mining_difficulty = data.get('mining_difficulty', 50)
        network_activity = data.get('network_activity', 0)
        
        # Check conditions
        if hashrate >= self.hashrate_threshold:
            if mining_difficulty >= self.mining_difficulty_threshold:
                if network_activity >= self.network_activity_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(hashrate, mining_difficulty, network_activity),
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
        
    def calculate_confidence(self, hashrate: float, mining_difficulty: float, network_activity: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Hashrate (0-0.35)
        if hashrate > 750000000:
            confidence += 0.35
        elif hashrate > 500000000:
            confidence += 0.15
            
        # Mining difficulty (0-0.35)
        if mining_difficulty > 70:
            confidence += 0.35
        elif mining_difficulty > 50:
            confidence += 0.15
            
        # Network activity (0-0.3)
        if network_activity > 1500000:
            confidence += 0.3
        elif network_activity > 1000000:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'hashrate_threshold': self.hashrate_threshold,
            'mining_difficulty_threshold': self.mining_difficulty_threshold,
            'network_activity_threshold': self.network_activity_threshold
        }
