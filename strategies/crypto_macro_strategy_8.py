"""
AlphaEdge Strategy – Crypto Macro Strategy 8
Monitors employment data and consumer spending for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy8:
    """
    Crypto Macro Strategy 8
    Uses employment data and consumer spending to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_8"
        self.name = "Crypto Macro Strategy 8"
        self.active = True
        
        # Strategy parameters
        self.unemployment_threshold = 4.0  # 4% unemployment
        self.jobs_growth_threshold = 100000  # 100K jobs
        self.retail_sales_threshold = 0.5  # 0.5% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        unemployment = data.get('unemployment_rate', 0)
        jobs_growth = data.get('jobs_growth', 0)
        retail_sales = data.get('retail_sales_growth', 0)
        
        # Check conditions
        if unemployment <= self.unemployment_threshold:
            if jobs_growth >= self.jobs_growth_threshold:
                if retail_sales >= self.retail_sales_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(unemployment, jobs_growth, retail_sales),
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
        
    def calculate_confidence(self, unemployment: float, jobs_growth: float, retail_sales: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Unemployment (0-0.35)
        if unemployment < 3.0:
            confidence += 0.35
        elif unemployment < 4.0:
            confidence += 0.15
            
        # Jobs growth (0-0.35)
        if jobs_growth > 200000:
            confidence += 0.35
        elif jobs_growth > 100000:
            confidence += 0.15
            
        # Retail sales (0-0.3)
        if retail_sales > 1.0:
            confidence += 0.3
        elif retail_sales > 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'unemployment_threshold': self.unemployment_threshold,
            'jobs_growth_threshold': self.jobs_growth_threshold,
            'retail_sales_threshold': self.retail_sales_threshold
        }
