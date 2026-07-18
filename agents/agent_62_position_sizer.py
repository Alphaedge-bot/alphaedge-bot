"""
AlphaEdge Agent 62 – Position Sizer
Dynamic sizing (2-6%), pyramiding (+20%/+50%/+100%/+200%), maximize return
V13.0.7 – UPDATED with Micro-Cap Position Sizing Review + Fractional Kelly
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PositionSizer:
    """Position Sizer – Calculates optimal position sizes"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "position_sizer"
        self.running = False
        
        # Configuration
        self.config = {
            'base_sizing': {
                'micro_cap': 0.02,
                'small_cap': 0.03,
                'mid_cap': 0.04,
                'large_cap': 0.05
            },
            'pyramiding': {
                'enabled': True,
                'max_additions': 4,
                'addition_1': 0.20,
                'addition_2': 0.50,
                'addition_3': 1.00,
                'addition_4': 2.00
            },
            'dynamic_sizing': {
                'by_regime': {'bull': 1.5, 'neutral': 1.0, 'bear': 0.5},
                'by_confidence': {'high': 1.2, 'medium': 1.0, 'low': 0.7}
            }
        }
        
        # ============================================
        # ITEM 24: MICRO-CAP POSITION SIZING REVIEW
        # ============================================
        self.micro_cap_sizing = {
            'enabled': True,
            'max_micro_cap_pct': 0.04,
            'min_micro_cap_pct': 0.01,
            'max_micro_cap_usd': 100000,
            'liquidity_adjustment': True,
            'volatility_adjustment': True
        }
        
        # ============================================
        # ITEM 32: FRACTIONAL KELLY
        # ============================================
        self.fractional_kelly = {
            'enabled': True,
            'fraction': 0.25,
            'max_kelly_pct': 0.10,
            'min_kelly_pct': 0.01,
            'lookback_trades': 50,
            'regime_adjustment': True
        }
        
    async def start(self):
        """Start the position sizer"""
        logger.info("Position Sizer starting...")
        self.running = True
        
        await self.event_bus.subscribe("position_size_request", self.handle_position_size_request)
        await self.event_bus.subscribe("pyramiding_check", self.handle_pyramiding_check)
        
        asyncio.create_task(self.run_sizing_cycle())
        logger.info("Position Sizer running")
        
    async def stop(self):
        """Stop the position sizer"""
        self.running = False
        logger.info("Position Sizer stopped")
        
    async def run_sizing_cycle(self):
        """Run regular sizing cycle"""
        while self.running:
            try:
                await self.update_sizing_parameters()
                await self.publish_sizing_update()
            except Exception as e:
                logger.error(f"Sizing cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 24: MICRO-CAP POSITION SIZING REVIEW
    # ============================================
    
    async def calculate_micro_cap_size(self, token: str, capital: float) -> float:
        """Calculate position size specifically for micro-caps"""
        if not self.micro_cap_sizing['enabled']:
            return capital * 0.02
        
        try:
            liquidity = await self._get_token_liquidity(token)
            volatility = await self._get_token_volatility(token)
            
            base_size = capital * 0.02
            
            if self.micro_cap_sizing['liquidity_adjustment']:
                liquidity_factor = min(liquidity / 1000000, 1.0)
                base_size *= (0.5 + 0.5 * liquidity_factor)
            
            if self.micro_cap_sizing['volatility_adjustment']:
                volatility_factor = max(1.0 - (volatility - 0.5) * 2, 0.5)
                base_size *= volatility_factor
            
            max_size = capital * self.micro_cap_sizing['max_micro_cap_pct']
            min_size = capital * self.micro_cap_sizing['min_micro_cap_pct']
            max_usd = self.micro_cap_sizing['max_micro_cap_usd']
            
            final_size = min(base_size, max_size, max_usd)
            final_size = max(final_size, min_size)
            
            return final_size
            
        except Exception as e:
            logger.error(f"Micro-cap sizing error: {e}")
            return capital * 0.02
    
    async def _get_token_liquidity(self, token: str) -> float:
        return 500000  # Simulated
    
    async def _get_token_volatility(self, token: str) -> float:
        return 0.4  # Simulated
    
    # ============================================
    # ITEM 32: FRACTIONAL KELLY
    # ============================================
    
    async def calculate_kelly_size(self, token: str, capital: float, regime: str = 'neutral') -> float:
        """Calculate position size using Fractional Kelly"""
        if not self.fractional_kelly['enabled']:
            return capital * 0.02
        
        try:
            performance = await self._get_token_performance(token)
            
            if performance['avg_win'] > 0:
                win_rate = performance['win_rate']
                loss_rate = 1 - win_rate
                win_loss_ratio = performance['avg_win'] / performance['avg_loss'] if performance['avg_loss'] > 0 else 1
                kelly_pct = win_rate - (loss_rate / win_loss_ratio)
                kelly_pct *= self.fractional_kelly['fraction']
                kelly_pct = min(kelly_pct, self.fractional_kelly['max_kelly_pct'])
                kelly_pct = max(kelly_pct, self.fractional_kelly['min_kelly_pct'])
                
                if self.fractional_kelly['regime_adjustment']:
                    regime_multiplier = self._get_regime_multiplier(regime)
                    kelly_pct *= regime_multiplier
                
                return capital * kelly_pct
                
        except Exception as e:
            logger.error(f"Kelly size calculation error: {e}")
            return capital * 0.02
    
    async def _get_token_performance(self, token: str) -> Dict:
        return {'win_rate': 0.65, 'avg_win': 0.08, 'avg_loss': 0.04, 'sharpe': 1.8, 'trades': 100}
    
    def _get_regime_multiplier(self, regime: str) -> float:
        multipliers = {'bull': 1.2, 'neutral': 1.0, 'bear': 0.8, 'crash': 0.5}
        return multipliers.get(regime, 1.0)
    
    # ============================================
    # MAIN SIZING METHODS
    # ============================================
    
    async def get_position_size(self, token: str, tier: str, capital: float, regime: str = 'neutral') -> float:
        """Get position size with micro-cap + Kelly adjustments"""
        # Apply Fractional Kelly
        kelly_size = await self.calculate_kelly_size(token, capital, regime)
        
        # Apply tier-specific caps
        if tier == 'micro_cap':
            micro_cap_size = await self.calculate_micro_cap_size(token, capital)
            return min(kelly_size, micro_cap_size)
        
        # For other tiers, use base sizing with Kelly
        base_pct = self.config['base_sizing'].get(tier, 0.03)
        base_size = capital * base_pct
        
        # Blend Kelly and base sizing
        blend_weight = 0.5
        blended_size = (kelly_size * blend_weight) + (base_size * (1 - blend_weight))
        
        # Apply caps
        max_size = capital * 0.08
        min_size = capital * 0.01
        
        return min(max(blended_size, min_size), max_size)
    
    async def get_pyramiding_size(self, token: str, current_size: float, addition_level: int) -> float:
        """Calculate pyramiding addition size"""
        if not self.config['pyramiding']['enabled']:
            return 0
            
        if addition_level > self.config['pyramiding']['max_additions']:
            return 0
            
        addition_key = f'addition_{addition_level}'
        addition_pct = self.config['pyramiding'].get(addition_key, 0)
        
        return current_size * addition_pct
    
    async def handle_position_size_request(self, event: Event):
        """Handle position size requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        token = event.data.get('token')
        tier = event.data.get('tier', 'mid_cap')
        capital = event.data.get('capital', 10000)
        regime = event.data.get('regime', 'neutral')
        
        size = await self.get_position_size(token, tier, capital, regime)
        
        response = Event(
            event_type="position_size_response",
            data={'request_id': request_id, 'token': token, 'size': size, 'tier': tier, 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_pyramiding_check(self, event: Event):
        """Handle pyramiding checks"""
        if not self.running:
            return
            
        token = event.data.get('token')
        current_size = event.data.get('current_size', 0)
        addition_level = event.data.get('addition_level', 1)
        
        addition_size = await self.get_pyramiding_size(token, current_size, addition_level)
        
        response = Event(
            event_type="pyramiding_response",
            data={'token': token, 'addition_size': addition_size, 'addition_level': addition_level, 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def update_sizing_parameters(self):
        """Update sizing parameters based on market conditions"""
        pass
        
    async def publish_sizing_update(self):
        """Publish sizing data update"""
        sizing_data = {
            'config': self.config,
            'micro_cap_sizing': self.micro_cap_sizing,
            'fractional_kelly': self.fractional_kelly,
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="sizing_update", data=sizing_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'config': self.config,
            'micro_cap_sizing': self.micro_cap_sizing,
            'fractional_kelly': self.fractional_kelly,
            'timestamp': datetime.now().isoformat()
        }
