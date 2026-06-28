"""
AlphaEdge Strategy – Solana Specific Strategy 8
Solana ecosystem developer activity analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SolanaSpecificStrategy8:
    """
    Solana Specific Strategy 8
    Analyzes Solana ecosystem developer activity
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "solana_specific_8"
        self.name = "Solana Specific Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.dev_activity_threshold = 100  # commits per week
        self.active_devs_threshold = 50
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        dev_activity = data.get('solana_dev_activity', 0)
        active_devs = data.get('solana_active_devs', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for developer activity signal
        if dev_activity > self.dev_activity_threshold:
            if active_devs > self.active_devs_threshold:
                if volume_ratio > self.volume_confirm:
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'developer_activity',
                        'confidence': self.calculate_confidence(dev_activity, active_devs),
                        'dev_activity': dev_activity,
                        'active_devs': active_devs,
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
        
    def calculate_confidence(self, dev_activity: float, active_devs: int) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Developer activity
        if dev_activity > 200:
            confidence += 0.2
        elif dev_activity > 100:
            confidence += 0.1
            
        # Active developers
        if active_devs > 100:
            confidence += 0.2
        elif active_devs > 50:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'dev_activity_threshold': self.dev_activity_threshold,
            'active_devs_threshold': self.active_devs_threshold
        }
