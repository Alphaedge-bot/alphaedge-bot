"""
AlphaEdge Strategy – Crypto Macro Strategy 13
Monitors technology sector and innovation for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy13:
    """
    Crypto Macro Strategy 13
    Uses technology sector and innovation to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_13"
        self.name = "Crypto Macro Strategy 13"
        self.active = True
        
        # Strategy parameters
        self.tech_sector_growth_threshold = 2.0  # 2% growth
        self.innovation_index_threshold = 50
        self.patent_filings_threshold = 100
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        tech_sector_growth = data.get('tech_sector_growth', 0)
        innovation_index = data.get('innovation_index', 50)
        patent_filings = data.get('patent_filings', 0)
        
        # Check conditions
        if tech_sector_growth >= self.tech_sector_growth_threshold:
            if innovation_index >= self.innovation_index_threshold:
                if patent_filings >= self.patent_filings_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(tech_sector_growth, innovation_index, patent_filings),
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
        
    def calculate_confidence(self, tech_sector_growth: float, innovation_index: float, patent_filings: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Tech sector growth (0-0.35)
        if tech_sector_growth > 3.0:
            confidence += 0.35
        elif tech_sector_growth > 2.0:
            confidence += 0.15
            
        # Innovation index (0-0.35)
        confidence += (innovation_index - 50) / 100 * 0.35
        
        # Patent filings (0-0.3)
        if patent_filings > 150:
            confidence += 0.3
        elif patent_filings > 100:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'tech_sector_growth_threshold': self.tech_sector_growth_threshold,
            'innovation_index_threshold': self.innovation_index_threshold,
            'patent_filings_threshold': self.patent_filings_threshold
        }
