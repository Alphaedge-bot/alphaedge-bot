"""
AlphaEdge Agent 62 – Position Sizer
Dynamic sizing (2-6%), pyramiding (+20%/+50%/+100%/+200%), maximize return
V13.0.7 – UPDATED with Micro-Cap Position Sizing Review + Fractional Kelly + Dynamic Kelly
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import math

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
        
        # ============================================
        # ITEM 26: DYNAMIC KELLY
        # ============================================
        self.dynamic_kelly = {
            'enabled': True,
            'regime_multipliers': {
                'bull': 1.2,
                'neutral': 1.0,
                'bear': 0.8,
                'crash': 0.5
            },
            'confidence_multipliers': {
                'high': 1.3,
                'medium': 1.0,
                'low': 0.6
            },
            'volatility_adj': True,
            'min_kelly_pct': 0.005,
            'max_kelly_pct': 0.12,
            'smoothing_window': 10
        }
        
        # Dynamic Kelly state
        self.kelly_history = {}  # token -> list of kelly values
        self.smoothed_kelly = {}  # token -> smoothed kelly
        
    async def start(self):
        """Start the position sizer"""
        logger.info("Position Sizer starting...")
        self.running = True
        
        await self.event_bus.subscribe("position_size_request", self.handle_position_size_request)
        await self.event_bus.subscribe("pyramiding_check", self.handle_pyramiding_check)
        await self.event_bus.subscribe("kelly_update", self.handle_kelly_update)
        
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
    # ITEM 26: DYNAMIC KELLY
    # ============================================
    
    async def calculate_dynamic_kelly(self, token: str, capital: float, regime: str, confidence: str) -> float:
        """
        Calculate Dynamic Kelly position size
        Item 26: Dynamic Kelly – Size = Kelly% × RegimeMultiplier × ConfidenceMultiplier
        """
        if not self.dynamic_kelly['enabled']:
            return capital * 0.02
        
        try:
            # 1. Get base Kelly from performance
            base_kelly_pct = await self._get_base_kelly(token)
            
            # 2. Apply regime multiplier
            regime_mult = self.dynamic_kelly['regime_multipliers'].get(regime, 1.0)
            
            # 3. Apply confidence multiplier
            conf_mult = self.dynamic_kelly['confidence_multipliers'].get(confidence, 1.0)
            
            # 4. Calculate dynamic Kelly percentage
            dynamic_kelly_pct = base_kelly_pct * regime_mult * conf_mult
            
            # 5. Apply volatility adjustment
            if self.dynamic_kelly['volatility_adj']:
                volatility = await self._get_token_volatility(token)
                vol_adj = max(0.5, 1.0 - volatility * 0.5)
                dynamic_kelly_pct *= vol_adj
            
            # 6. Apply caps
            dynamic_kelly_pct = min(dynamic_kelly_pct, self.dynamic_kelly['max_kelly_pct'])
            dynamic_kelly_pct = max(dynamic_kelly_pct, self.dynamic_kelly['min_kelly_pct'])
            
            # 7. Smooth the Kelly value
            smoothed_pct = await self._smooth_kelly(token, dynamic_kelly_pct)
            
            # 8. Calculate final size
            size = capital * smoothed_pct
            
            # 9. Apply micro-cap caps
            tier = await self._get_token_tier(token)
            if tier == 'micro_cap':
                micro_cap_size = await self.calculate_micro_cap_size(token, capital)
                size = min(size, micro_cap_size)
            
            # 10. Apply hard caps
            max_size = capital * 0.10
            min_size = capital * 0.005
            
            return min(max(size, min_size), max_size)
            
        except Exception as e:
            logger.error(f"Dynamic Kelly calculation error: {e}")
            return capital * 0.02
    
    async def _get_base_kelly(self, token: str) -> float:
        """Get base Kelly percentage from performance"""
        performance = await self._get_token_performance(token)
        
        if performance['avg_win'] <= 0:
            return 0.02
        
        win_rate = performance['win_rate']
        loss_rate = 1 - win_rate
        win_loss_ratio = performance['avg_win'] / performance['avg_loss'] if performance['avg_loss'] > 0 else 1
        
        kelly_pct = win_rate - (loss_rate / win_loss_ratio)
        
        # Apply Fractional Kelly (Item 32)
        kelly_pct *= self.fractional_kelly['fraction']
        
        # Apply baseline caps
        kelly_pct = min(kelly_pct, self.fractional_kelly['max_kelly_pct'])
        kelly_pct = max(kelly_pct, self.fractional_kelly['min_kelly_pct'])
        
        return kelly_pct
    
    async def _smooth_kelly(self, token: str, new_kelly: float) -> float:
        """Smooth Kelly values to prevent sudden jumps"""
        if token not in self.kelly_history:
            self.kelly_history[token] = []
        
        self.kelly_history[token].append(new_kelly)
        
        # Keep last N values
        window = self.dynamic_kelly['smoothing_window']
        if len(self.kelly_history[token]) > window:
            self.kelly_history[token] = self.kelly_history[token][-window:]
        
        # Calculate smoothed value (simple moving average)
        smoothed = sum(self.kelly_history[token]) / len(self.kelly_history[token])
        self.smoothed_kelly[token] = smoothed
        
        return smoothed
    
    async def _get_token_tier(self, token: str) -> str:
        """Get token tier from state"""
        # In production, fetch from state
        return 'mid_cap'
    
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
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def _get_token_liquidity(self, token: str) -> float:
        """Get token liquidity"""
        return 500000  # Simulated
    
    async def _get_token_volatility(self, token: str) -> float:
        """Get token volatility (0-1)"""
        return 0.3  # Simulated
    
    async def _get_token_performance(self, token: str) -> Dict:
        """Get token performance for Kelly calculation"""
        return {
            'win_rate': 0.65,
            'avg_win': 0.08,
            'avg_loss': 0.04,
            'sharpe': 1.8,
            'trades': 100
        }
    
    # ============================================
    # MAIN SIZING METHODS
    # ============================================
    
    async def get_position_size(self, token: str, tier: str, capital: float, 
                                regime: str = 'neutral', confidence: str = 'medium') -> float:
        """
        Get position size with Dynamic Kelly
        Item 26: Dynamic Kelly integration
        """
        # Step 1: Calculate Dynamic Kelly
        kelly_size = await self.calculate_dynamic_kelly(token, capital, regime, confidence)
        
        # Step 2: Get base sizing
        base_pct = self.config['base_sizing'].get(tier, 0.03)
        base_size = capital * base_pct
        
        # Step 3: Blend Kelly and base sizing
        # Higher confidence = more weight to Kelly
        if confidence == 'high':
            kelly_weight = 0.7
        elif confidence == 'medium':
            kelly_weight = 0.5
        else:
            kelly_weight = 0.3
        
        blended_size = (kelly_size * kelly_weight) + (base_size * (1 - kelly_weight))
        
        # Step 4: Apply tier-specific caps
        if tier == 'micro_cap':
            micro_cap_size = await self.calculate_micro_cap_size(token, capital)
            blended_size = min(blended_size, micro_cap_size)
        
        # Step 5: Apply hard caps
        max_size = capital * 0.10
        min_size = capital * 0.005
        
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
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_position_size_request(self, event: Event):
        """Handle position size requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        token = event.data.get('token')
        tier = event.data.get('tier', 'mid_cap')
        capital = event.data.get('capital', 10000)
        regime = event.data.get('regime', 'neutral')
        confidence = event.data.get('confidence', 'medium')
        
        size = await self.get_position_size(token, tier, capital, regime, confidence)
        
        response = Event(
            event_type="position_size_response",
            data={
                'request_id': request_id,
                'token': token,
                'size': size,
                'tier': tier,
                'regime': regime,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            },
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
            data={
                'token': token,
                'addition_size': addition_size,
                'addition_level': addition_level,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_kelly_update(self, event: Event):
        """Handle Kelly updates"""
        if not self.running:
            return
            
        token = event.data.get('token')
        kelly_value = event.data.get('kelly_value', 0)
        
        if token:
            await self._smooth_kelly(token, kelly_value)
            
    async def update_sizing_parameters(self):
        """Update sizing parameters based on market conditions"""
        pass
        
    async def publish_sizing_update(self):
        """Publish sizing data update"""
        sizing_data = {
            'config': self.config,
            'micro_cap_sizing': self.micro_cap_sizing,
            'fractional_kelly': self.fractional_kelly,
            'dynamic_kelly': self.dynamic_kelly,
            'smoothed_kelly': self.smoothed_kelly,
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="sizing_update", data=sizing_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get position sizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'config': self.config,
            'micro_cap_sizing': self.micro_cap_sizing,
            'fractional_kelly': self.fractional_kelly,
            'dynamic_kelly': self.dynamic_kelly,
            'kelly_history_count': len(self.kelly_history),
            'smoothed_kelly_count': len(self.smoothed_kelly),
            'timestamp': datetime.now().isoformat()
        }
