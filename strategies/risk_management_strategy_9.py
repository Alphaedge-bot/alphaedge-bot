"""
AlphaEdge Strategy – Risk Management Strategy 9
Liquidity risk and order book depth analysis
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RiskManagementStrategy9:
    """
    Risk Management Strategy 9
    Analyzes liquidity risk and order book depth
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "risk_management_9"
        self.name = "Risk Management Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.liquidity_threshold = 1000  # tokens
        self.depth_threshold = 0.5  # 50%
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        liquidity = data.get('liquidity', 0)
        book_depth = data.get('book_depth', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        # Check for low liquidity risk
        if liquidity < self.liquidity_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'reduce_position',
                    'confidence': self.calculate_confidence(liquidity, 'liquidity'),
                    'timestamp': datetime.now().isoformat()
                }
                signal_event = Event(
                    event_type="signal_generated",
                    data=signal,
                    source=self.strategy_id
                )
                await self.event_bus.publish(signal_event)
                
        # Check order book depth
        if book_depth < self.depth_threshold:
            if volume_ratio > self.volume_confirm:
                signal = {
                    'strategy': self.strategy_id,
                    'type': 'limit_orders',
                    'confidence': self.calculate_confidence(book_depth, 'depth'),
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
        
    def calculate_confidence(self, value: float, risk_type: str) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        if risk_type == 'liquidity':
            if value < 100:
                confidence += 0.3
            elif value < 1000:
                confidence += 0.15
                
        elif risk_type == 'depth':
            if value < 0.2:
                confidence += 0.3
            elif value < 0.5:
                confidence += 0.15
                
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'liquidity_threshold': self.liquidity_threshold,
            'depth_threshold': self.depth_threshold
        }
