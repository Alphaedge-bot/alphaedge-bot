"""
AlphaEdge Strategy – Profit Taking Strategies Strategy 7
Time-based profit taking
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingStrategiesStrategy7:
    """
    Profit Taking Strategies Strategy 7
    Bases profit taking on holding time
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "profit_taking_strategies_7"
        self.name = "Profit Taking Strategies Strategy 7"
        self.active = True
        
        # Strategy parameters
        self.max_hold_time = 14  # days
        self.volume_confirm = 1.2
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("market_data_update", self.handle_market_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_market_data(self, event: Event):
        """Handle market data updates"""
        data = event.data
        entry_time = data.get('entry_time')
        price = data.get('price', 0)
        entry_price = data.get('entry_price', 0)
        volume = data.get('volume', 0)
        volume_ma = data.get('volume_ma', 1)
        
        volume_ratio = volume / volume_ma if volume_ma > 0 else 1
        
        if entry_time:
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                hold_time = (datetime.now() - entry_dt).days
                
                # Check if hold time exceeded
                if hold_time >= self.max_hold_time:
                    gain = (price - entry_price) / entry_price if entry_price > 0 else 0
                    
                    if gain > 0.02:  # At least 2% gain
                        if volume_ratio > self.volume_confirm:
                            signal = {
                                'strategy': self.strategy_id,
                                'type': 'time_based_take_profit',
                                'confidence': self.calculate_confidence(hold_time, gain),
                                'hold_time': hold_time,
                                'gain': gain,
                                'timestamp': datetime.now().isoformat()
                            }
                            signal_event = Event(
                                event_type="signal_generated",
                                data=signal,
                                source=self.strategy_id
                            )
                            await self.event_bus.publish(signal_event)
            except:
                pass
                
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
        
    def calculate_confidence(self, hold_time: int, gain: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Hold time
        if hold_time > 14:
            confidence += 0.2
        elif hold_time > 10:
            confidence += 0.1
            
        # Gain
        if gain > 0.15:
            confidence += 0.2
        elif gain > 0.1:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'max_hold_time': self.max_hold_time
        }
