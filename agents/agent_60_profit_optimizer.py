"""
AlphaEdge Agent 60 – Profit Optimizer
Dynamic take-profit, bull run trend detection (probabilistic), pyramiding optimizer
V13.0.7 – UPDATED with Let Winners Run (Item 28)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitOptimizer:
    """
    Profit Optimizer – Dynamic take-profit and bull run detection
    V13.0.7 – Item 28: Let Winners Run
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "profit_optimizer"
        self.running = False
        
        # Configuration
        self.config = {
            'take_profit': {
                'enabled': True,
                'targets': {
                    'tier_1': 0.15,
                    'tier_2': 0.25,
                    'tier_3': 0.50,
                    'tier_4': 1.00
                },
                'partial_take_profit': {
                    'tier_1': 0.25,
                    'tier_2': 0.25,
                    'tier_3': 0.25,
                    'tier_4': 0.25
                }
            },
            'trailing_stop': {
                'enabled': True,
                'activation': 0.05,
                'trail_by': 0.005,
                'micro_cap_activation': 0.03
            }
        }
        
        # ============================================
        # ITEM 28: LET WINNERS RUN CONFIGURATION
        # ============================================
        self.let_winners_run = {
            'enabled': True,
            'conditions': {
                'min_tps': 85.0,
                'min_days': 3,
                'mcdx_golden_cross_required': True,
                'smc_bullish_required': True
            },
            'actions': {
                'remove_tp3': True,
                'remove_tp4': True,
                'trail_only': True,
                'trail_percent': 0.08
            },
            're_entry': {
                'enabled': True,
                'min_tps': 80.0,
                'max_retrace': 0.50,
                'position_size_reduction': 0.50
            },
            'bull_run': {
                'detection': {
                    'parabolic_threshold': 0.30,
                    'volume_spike_threshold': 2.0,
                    'new_ath_threshold': 0.10
                },
                'confidence_min': 0.70
            }
        }
        
        # Position tracking for Let Winners Run
        self.winner_positions = {}  # token -> {entry_tps, entry_time, removed_tp3, removed_tp4}
        self.bull_run_detected = {}
        self.profit_history = {}
        
    async def start(self):
        """Start the profit optimizer"""
        logger.info("Profit Optimizer starting...")
        self.running = True
        
        await self.event_bus.subscribe("profit_optimize_request", self.handle_profit_optimize_request)
        await self.event_bus.subscribe("position_updated", self.handle_position_updated)
        await self.event_bus.subscribe("market_regime_change", self.handle_regime_change)
        
        asyncio.create_task(self.run_optimization_cycle())
        logger.info("Profit Optimizer running")
        
    async def stop(self):
        """Stop the profit optimizer"""
        self.running = False
        logger.info("Profit Optimizer stopped")
        
    async def run_optimization_cycle(self):
        """Run regular optimization cycle"""
        while self.running:
            try:
                await self.check_winners()
                await self.detect_bull_runs()
                await self.optimize_take_profits()
                await self.publish_optimization_status()
            except Exception as e:
                logger.error(f"Optimization cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 28: LET WINNERS RUN
    # ============================================
    
    async def check_winners(self):
        """
        Check if any positions qualify for Let Winners Run
        Item 28: Let Winners Run logic
        """
        if not self.let_winners_run['enabled']:
            return
            
        positions = await self.state_manager.get('positions', {})
        
        for token, position in positions.items():
            # 1. Check if position is already a winner
            if token in self.winner_positions:
                # Check if still qualifies
                await self._maintain_winner_status(token, position)
                continue
            
            # 2. Check if position qualifies as a winner
            qualifies = await self._check_winner_qualification(token, position)
            
            if qualifies:
                logger.info(f"🏆 {token} qualifies for Let Winners Run!")
                await self._activate_winner_status(token, position)
                
    async def _check_winner_qualification(self, token: str, position: Dict) -> bool:
        """
        Check if position qualifies for Let Winners Run
        Conditions:
        - TPS ≥85 for 3+ days
        - MCDX Golden Cross active
        - SMC Bullish confirmed
        """
        try:
            # 1. Check TPS
            tps_data = await self.state_manager.get(f'tps_history_{token}', [])
            if len(tps_data) < 3:
                return False
                
            recent_tps = tps_data[-3:]
            if not all(t >= self.let_winners_run['conditions']['min_tps'] for t in recent_tps):
                return False
                
            # 2. Check MCDX Golden Cross
            mcdx_signal = await self.state_manager.get(f'mcdx_signal_{token}', {})
            if self.let_winners_run['conditions']['mcdx_golden_cross_required']:
                if not mcdx_signal.get('golden_cross', False):
                    return False
                    
            # 3. Check SMC Bullish
            smc_signal = await self.state_manager.get(f'smc_signal_{token}', {})
            if self.let_winners_run['conditions']['smc_bullish_required']:
                if not smc_signal.get('bos_bullish', False):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Winner qualification check error: {e}")
            return False
            
    async def _activate_winner_status(self, token: str, position: Dict):
        """
        Activate winner status for a position
        Actions:
        - Remove TP3/TP4
        - Switch to trailing stop only
        """
        self.winner_positions[token] = {
            'entry_tps': position.get('tps', 0),
            'entry_time': datetime.now().isoformat(),
            'removed_tp3': False,
            'removed_tp4': False,
            'activated': datetime.now().isoformat()
        }
        
        # 1. Remove TP3 and TP4
        if self.let_winners_run['actions']['remove_tp3']:
            await self._remove_take_profit(token, 3)
            self.winner_positions[token]['removed_tp3'] = True
            
        if self.let_winners_run['actions']['remove_tp4']:
            await self._remove_take_profit(token, 4)
            self.winner_positions[token]['removed_tp4'] = True
            
        # 2. Set trailing stop only
        if self.let_winners_run['actions']['trail_only']:
            await self._set_trailing_only(token)
            
        # 3. Notify
        await self.event_bus.publish(Event(
            event_type="winner_activated",
            data={
                'token': token,
                'entry_tps': position.get('tps', 0),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        ))
        
        logger.info(f"✅ Winner status activated for {token}")
        
    async def _maintain_winner_status(self, token: str, position: Dict):
        """
        Maintain winner status for a position
        """
        # Check if still qualifies
        qualifies = await self._check_winner_qualification(token, position)
        
        if not qualifies:
            logger.info(f"⚠️ {token} no longer qualifies for Let Winners Run")
            await self._deactivate_winner_status(token)
            
    async def _deactivate_winner_status(self, token: str):
        """
        Deactivate winner status for a position
        """
        if token in self.winner_positions:
            # Restore TP3/TP4
            await self._restore_take_profit(token, 3)
            await self._restore_take_profit(token, 4)
            
            del self.winner_positions[token]
            logger.info(f"❌ Winner status deactivated for {token}")
            
    async def _remove_take_profit(self, token: str, tier: int):
        """Remove a take profit target"""
        logger.info(f"Removed TP{tier} for {token}")
        await self.state_manager.set(f'tp_removed_{token}_{tier}', True)
        
    async def _restore_take_profit(self, token: str, tier: int):
        """Restore a take profit target"""
        await self.state_manager.set(f'tp_removed_{token}_{tier}', False)
        
    async def _set_trailing_only(self, token: str):
        """Set trailing stop only for a position"""
        await self.state_manager.set(f'trailing_only_{token}', True)
        
    # ============================================
    # BULL RUN DETECTION (Item 28)
    # ============================================
    
    async def detect_bull_runs(self):
        """
        Detect bull runs to optimize exits
        Item 28: Bull run detection
        """
        positions = await self.state_manager.get('positions', {})
        
        for token, position in positions.items():
            bull_run_score = await self._calculate_bull_run_score(token)
            confidence = bull_run_score.get('confidence', 0)
            
            if confidence >= self.let_winners_run['bull_run']['confidence_min']:
                if token not in self.bull_run_detected:
                    logger.info(f"🚀 Bull run detected for {token}")
                    self.bull_run_detected[token] = bull_run_score
                    
                    # Update exit strategy for bull run
                    await self._adjust_for_bull_run(token)
            else:
                if token in self.bull_run_detected:
                    del self.bull_run_detected[token]
                    
    async def _calculate_bull_run_score(self, token: str) -> Dict:
        """
        Calculate bull run detection score
        """
        score = 0.0
        reasons = []
        
        try:
            # 1. Parabolic move
            price_history = await self.state_manager.get(f'price_history_{token}', [])
            if len(price_history) >= 5:
                recent_move = (price_history[-1] - price_history[-5]) / price_history[-5]
                if recent_move > self.let_winners_run['bull_run']['detection']['parabolic_threshold']:
                    score += 0.4
                    reasons.append('parabolic_move')
                    
            # 2. Volume spike
            volume_history = await self.state_manager.get(f'volume_history_{token}', [])
            if len(volume_history) >= 5:
                avg_volume = sum(volume_history[-5:]) / 5
                volume_spike = volume_history[-1] / avg_volume
                if volume_spike > self.let_winners_run['bull_run']['detection']['volume_spike_threshold']:
                    score += 0.3
                    reasons.append('volume_spike')
                    
            # 3. New ATH
            all_time_high = await self.state_manager.get(f'all_time_high_{token}', 0)
            current_price = price_history[-1] if price_history else 0
            if all_time_high > 0:
                ath_break = (current_price - all_time_high) / all_time_high
                if ath_break > self.let_winners_run['bull_run']['detection']['new_ath_threshold']:
                    score += 0.3
                    reasons.append('new_ath')
                    
            # 4. MCDX Golden Cross
            mcdx_signal = await self.state_manager.get(f'mcdx_signal_{token}', {})
            if mcdx_signal.get('golden_cross', False):
                score += 0.15
                reasons.append('golden_cross')
                
            # 5. SMC Bullish
            smc_signal = await self.state_manager.get(f'smc_signal_{token}', {})
            if smc_signal.get('bos_bullish', False):
                score += 0.15
                reasons.append('bos_bullish')
                
        except Exception as e:
            logger.error(f"Bull run score error: {e}")
            
        return {
            'confidence': min(score, 1.0),
            'score': score,
            'reasons': reasons
        }
        
    async def _adjust_for_bull_run(self, token: str):
        """
        Adjust exit strategy for bull run
        """
        # Extend trailing stop
        await self.state_manager.set(f'trailing_pct_{token}', 0.10)
        logger.info(f"📈 Extended trailing stop for {token} to 10%")
        
    # ============================================
    # RE-ENTRY (Item 28)
    # ============================================
    
    async def check_re_entry(self, token: str, current_price: float, entry_price: float) -> Dict:
        """
        Check if re-entry is available
        Item 28: Re-entry after partial sell
        """
        result = {
            'available': False,
            'reason': '',
            'size': 0.0
        }
        
        if not self.let_winners_run['re_entry']['enabled']:
            return result
            
        try:
            # 1. Check TPS
            tps = await self.state_manager.get(f'tps_{token}', 0)
            if tps < self.let_winners_run['re_entry']['min_tps']:
                result['reason'] = f'TPS {tps} below minimum'
                return result
                
            # 2. Check retracement
            retrace = (current_price - entry_price) / entry_price
            if retrace > 0:
                # Price moved up, check retracement
                max_price = await self.state_manager.get(f'max_price_{token}', entry_price)
                retrace_from_high = (max_price - current_price) / max_price
                
                if retrace_from_high > self.let_winners_run['re_entry']['max_retrace']:
                    result['available'] = True
                    result['reason'] = f'Retrace {retrace_from_high:.2%} from high'
                    result['size'] = self.let_winners_run['re_entry']['position_size_reduction']
                    
        except Exception as e:
            logger.error(f"Re-entry check error: {e}")
            
        return result
        
    # ============================================
    # TAKE PROFIT OPTIMIZATION
    # ============================================
    
    async def optimize_take_profits(self):
        """Optimize take profit levels"""
        if not self.config['take_profit']['enabled']:
            return
            
        positions = await self.state_manager.get('positions', {})
        
        for token, position in positions.items():
            # Check if in bull run
            if token in self.bull_run_detected:
                # Extend take profits in bull run
                await self._extend_take_profits(token)
                
    async def _extend_take_profits(self, token: str):
        """Extend take profit targets in bull run"""
        current_targets = self.config['take_profit']['targets']
        
        # Extend by 20% in bull run
        extended_targets = {
            'tier_1': current_targets['tier_1'] * 1.2,
            'tier_2': current_targets['tier_2'] * 1.2,
            'tier_3': current_targets['tier_3'] * 1.2,
            'tier_4': current_targets['tier_4'] * 1.2
        }
        
        await self.state_manager.set(f'extended_tp_{token}', extended_targets)
        
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_profit_optimize_request(self, event: Event):
        """Handle profit optimization requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        request_id = event.data.get('request_id')
        
        if token:
            # Check if token is a winner
            is_winner = token in self.winner_positions
            bull_run = token in self.bull_run_detected
            
            response = Event(
                event_type="profit_optimize_response",
                data={
                    'request_id': request_id,
                    'token': token,
                    'is_winner': is_winner,
                    'bull_run_detected': bull_run,
                    'winner_data': self.winner_positions.get(token),
                    'bull_run_data': self.bull_run_detected.get(token),
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id,
                target=event.source
            )
            await self.event_bus.publish(response)
            
    async def handle_position_updated(self, event: Event):
        """Handle position updates"""
        if not self.running:
            return
            
        token = event.data.get('token')
        position = event.data.get('position', {})
        
        if token:
            # Update profit history
            pnl = position.get('pnl_percent', 0)
            if token not in self.profit_history:
                self.profit_history[token] = []
            self.profit_history[token].append(pnl)
            
            # Keep last 100 entries
            if len(self.profit_history[token]) > 100:
                self.profit_history[token] = self.profit_history[token][-100:]
                
    async def handle_regime_change(self, event: Event):
        """Handle market regime changes"""
        if not self.running:
            return
            
        regime = event.data.get('regime', 'neutral')
        
        # Adjust bullish run detection thresholds for regime
        if regime == 'bull':
            self.let_winners_run['bull_run']['confidence_min'] = 0.60
        else:
            self.let_winners_run['bull_run']['confidence_min'] = 0.70
            
    async def publish_optimization_status(self):
        """Publish optimization status"""
        status_data = {
            'winner_positions': len(self.winner_positions),
            'bull_run_detected': len(self.bull_run_detected),
            'let_winners_run_enabled': self.let_winners_run['enabled'],
            'winner_tokens': list(self.winner_positions.keys()),
            'bull_run_tokens': list(self.bull_run_detected.keys()),
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="profit_optimizer_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get profit optimizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'winner_positions': len(self.winner_positions),
            'bull_run_detected': len(self.bull_run_detected),
            'winner_tokens': list(self.winner_positions.keys()),
            'bull_run_tokens': list(self.bull_run_detected.keys()),
            'let_winners_run_enabled': self.let_winners_run['enabled'],
            'timestamp': datetime.now().isoformat()
              }
