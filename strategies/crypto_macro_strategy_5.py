"""
AlphaEdge Strategy – Crypto Macro Strategy 5
Monitors inflation and purchasing power for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy5:
    """
    Crypto Macro Strategy 5
    Uses inflation and purchasing power to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_5"
        self.name = "Crypto Macro Strategy 5"
        self.active = True
        
        # Strategy parameters
        self.inflation_threshold = 3.0  # 3% inflation
        self.ppi_threshold = 2.5       # 2.5% PPI
        self.cpi_trend_threshold = 0.5  # 0.5% change
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        inflation = data.get('inflation_rate', 0)
        ppi = data.get('ppi', 0)
        cpi_trend = data.get('cpi_trend', 0)
        
        # Check conditions
        if inflation <= self.inflation_threshold:
            if ppi <= self.ppi_threshold:
                if cpi_trend <= self.cpi_trend_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(inflation, ppi, cpi_trend),
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
        
    def calculate_confidence(self, inflation: float, ppi: float, cpi_trend: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Inflation (0-0.4)
        if inflation < 2.0:
            confidence += 0.4
        elif inflation < 3.0:
            confidence += 0.2
            
        # PPI (0-0.3)
        if ppi < 2.0:
            confidence += 0.3
        elif ppi < 2.5:
            confidence += 0.15
            
        # CPI trend (0-0.3)
        if cpi_trend < 0:
            confidence += 0.3
        elif cpi_trend < 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'inflation_threshold': self.inflation_threshold,
            'ppi_threshold': self.ppi_threshold,
            'cpi_trend_threshold': self.cpi_trend_threshold
        }
