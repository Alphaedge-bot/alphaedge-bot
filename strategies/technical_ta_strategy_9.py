"""
AlphaEdge Strategy – Technical TA Strategy 9
Ichomoku Cloud trend analysis and signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechnicalTAStrategy9:
    """
    Technical TA Strategy 9
    Uses Ichimoku Cloud for trend analysis and signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "technical_ta_9"
        self.name = "Technical TA Strategy 9"
        self.active = True
        
        # Strategy parameters
        self.tenkan_period = 9
        self.kijun_period = 26
        self.senkou_span_b_period = 52
        self.chikou_span_period = 26
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        await self.event_bus.subscribe("price_data_update", self.handle_price_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_price_data(self, event: Event):
        """Handle price data updates"""
        data = event.data
        price = data.get('price', 0)
        tenkan = data.get('tenkan_sen', 0)
        kijun = data.get('kijun_sen', 0)
        senkou_a = data.get('senkou_span_a', 0)
        senkou_b = data.get('senkou_span_b', 0)
        chikou = data.get('chikou_span', 0)
        
        # Check for bullish cloud breakout
        if price > senkou_a and price > senkou_b and tenkan > kijun:
            signal = {
                'strategy': self.strategy_id,
                'type': 'buy',
                'confidence': self.calculate_confidence(price, tenkan, kijun, senkou_a, senkou_b),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for bearish cloud breakdown
        elif price < senkou_a and price < senkou_b and tenkan < kijun:
            signal = {
                'strategy': self.strategy_id,
                'type': 'sell',
                'confidence': self.calculate_confidence(price, tenkan, kijun, senkou_a, senkou_b),
                'timestamp': datetime.now().isoformat()
            }
            signal_event = Event(
                event_type="signal_generated",
                data=signal,
                source=self.strategy_id
            )
            await self.event_bus.publish(signal_event)
            
        # Check for cloud twist (potential breakout)
        elif tenkan > kijun and senkou_a > senkou_b:
            signal = {
                'strategy': self.strategy_id,
                'type': 'watch',
                'confidence': 0.5,
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
        
    def calculate_confidence(self, price: float, tenkan: float, kijun: float, senkou_a: float, senkou_b: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Tenkan/Kijun crossover
        tk_spread = abs(tenkan - kijun) / kijun
        if tk_spread > 0.02:
            confidence += 0.2
        elif tk_spread > 0.01:
            confidence += 0.1
            
        # Cloud thickness
        cloud_thickness = abs(senkou_a - senkou_b) / senkou_a
        if cloud_thickness > 0.05:
            confidence += 0.2
        elif cloud_thickness > 0.02:
            confidence += 0.1
            
        # Price vs cloud
        if price > max(senkou_a, senkou_b) * 1.02:
            confidence += 0.1
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tenkan_period': self.tenkan_period,
            'kijun_period': self.kijun_period
        }
