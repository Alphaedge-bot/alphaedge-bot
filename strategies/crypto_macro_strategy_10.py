"""
AlphaEdge Strategy – Crypto Macro Strategy 10
Monitors credit markets and liquidity for crypto signals
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CryptoMacroStrategy10:
    """
    Crypto Macro Strategy 10
    Uses credit markets and liquidity to generate signals
    """
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.strategy_id = "crypto_macro_10"
        self.name = "Crypto Macro Strategy 10"
        self.active = True
        
        # Strategy parameters
        self.credit_spread_threshold = 2.0  # 2% spread
        self.liquidity_index_threshold = 50
        self.bank_lending_threshold = 0.5  # 0.5% growth
        
    async def start(self):
        """Start strategy"""
        logger.info(f"Strategy {self.name} started")
        
        # Subscribe to macro updates
        await self.event_bus.subscribe("macro_data_update", self.handle_macro_data)
        await self.event_bus.subscribe("signal_request", self.handle_signal_request)
        
    async def handle_macro_data(self, event: Event):
        """Handle macro data updates"""
        data = event.data
        credit_spread = data.get('credit_spread', 0)
        liquidity_index = data.get('liquidity_index', 50)
        bank_lending = data.get('bank_lending_growth', 0)
        
        # Check conditions
        if credit_spread <= self.credit_spread_threshold:
            if liquidity_index >= self.liquidity_index_threshold:
                if bank_lending >= self.bank_lending_threshold:
                    # Generate buy signal
                    signal = {
                        'strategy': self.strategy_id,
                        'type': 'buy',
                        'confidence': self.calculate_confidence(credit_spread, liquidity_index, bank_lending),
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
        
    def calculate_confidence(self, credit_spread: float, liquidity_index: float, bank_lending: float) -> float:
        """Calculate signal confidence"""
        confidence = 0.5
        
        # Credit spread (0-0.35)
        if credit_spread < 1.0:
            confidence += 0.35
        elif credit_spread < 2.0:
            confidence += 0.15
            
        # Liquidity index (0-0.35)
        confidence += (liquidity_index - 50) / 100 * 0.35
        
        # Bank lending (0-0.3)
        if bank_lending > 1.0:
            confidence += 0.3
        elif bank_lending > 0.5:
            confidence += 0.15
            
        return min(1.0, max(0, confidence))
        
    async def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'active': self.active,
            'credit_spread_threshold': self.credit_spread_threshold,
            'liquidity_index_threshold': self.liquidity_index_threshold,
            'bank_lending_threshold': self.bank_lending_threshold
        }
