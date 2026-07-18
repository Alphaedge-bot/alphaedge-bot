"""
AlphaEdge Agent 70 – Early Exit Blocker
Block premature exits (ADX>40 block, TPS≥82 block, higher highs intact)
V13.0.7 – UPDATED with Let Winners Run Veto Power (Item 28)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class EarlyExitBlocker:
    """
    Early Exit Blocker – Blocks premature exits
    V13.0.7 – Item 28: Let Winners Run Veto Power
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "early_exit_blocker"
        self.running = False
        
        # Configuration
        self.config = {
            'block_conditions': {
                'adx_threshold': 40,
                'tps_threshold': 82,
                'higher_highs_required': True,
                'higher_lows_required': True
            },
            'exceptions': {
                'stop_loss_hit': True,
                'drawdown_exceeded': True,
                'emergency': True
            }
        }
        
        # ============================================
        # ITEM 28: LET WINNERS RUN VETO POWER
        # ============================================
        self.let_winners_run_veto = {
            'enabled': True,
            'veto_conditions': {
                'tps_above': 85,
                'mcdx_golden_cross': True,
                'smc_bullish': True,
                'adx_trending': 25
            },
            'actions': {
                'veto_exit': True,
                'adjust_sl': True,
                'send_alert': True
            }
        }
        
        # Track blocked exits
        self.blocked_exits = {}
        self.vetoed_exits = {}
        
    async def start(self):
        """Start the early exit blocker"""
        logger.info("Early Exit Blocker starting...")
        self.running = True
        
        await self.event_bus.subscribe("exit_request", self.handle_exit_request)
        await self.event_bus.subscribe("position_update", self.handle_position_update)
        
        asyncio.create_task(self.run_blocker_cycle())
        logger.info("Early Exit Blocker running")
        
    async def stop(self):
        """Stop the early exit blocker"""
        self.running = False
        logger.info("Early Exit Blocker stopped")
        
    async def run_blocker_cycle(self):
        """Run regular blocker cycle"""
        while self.running:
            try:
                await self.check_blocked_exits()
                await self.publish_blocker_status()
            except Exception as e:
                logger.error(f"Blocker cycle error: {e}")
            await asyncio.sleep(30)
            
    # ============================================
    # ITEM 28: LET WINNERS RUN VETO
    # ============================================
    
    async def check_let_winners_run_veto(self, token: str, exit_request: Dict) -> Dict:
        """
        Check if exit should be vetoed by Let Winners Run
        Item 28: Veto power for winners
        """
        result = {
            'vetoed': False,
            'reason': '',
            'action': 'allow'
        }
        
        if not self.let_winners_run_veto['enabled']:
            return result
            
        try:
            # 1. Check if token is a winner (in Let Winners Run)
            is_winner = await self.state_manager.get(f'winner_{token}', False)
            if not is_winner:
                return result
                
            # 2. Check veto conditions
            tps = await self.state_manager.get(f'tps_{token}', 0)
            mcdx_signal = await self.state_manager.get(f'mcdx_signal_{token}', {})
            smc_signal = await self.state_manager.get(f'smc_signal_{token}', {})
            adx = await self.state_manager.get(f'adx_{token}', 20)
            
            veto_active = True
            
            if self.let_winners_run_veto['veto_conditions']['tps_above']:
                if tps < self.let_winners_run_veto['veto_conditions']['tps_above']:
                    veto_active = False
                    
            if self.let_winners_run_veto['veto_conditions']['mcdx_golden_cross']:
                if not mcdx_signal.get('golden_cross', False):
                    veto_active = False
                    
            if self.let_winners_run_veto['veto_conditions']['smc_bullish']:
                if not smc_signal.get('bos_bullish', False):
                    veto_active = False
                    
            if self.let_winners_run_veto['veto_conditions']['adx_trending']:
                if adx < self.let_winners_run_veto['veto_conditions']['adx_trending']:
                    veto_active = False
                    
            # 3. Apply veto
            if veto_active:
                result['vetoed'] = True
                result['reason'] = f'Let Winners Run active (TPS={tps}, ADX={adx})'
                result['action'] = 'block'
                
                if self.let_winners_run_veto['actions']['send_alert']:
                    await self.event_bus.publish(Event(
                        event_type="exit_vetoed",
                        data={
                            'token': token,
                            'reason': result['reason'],
                            'timestamp': datetime.now().isoformat()
                        },
                        source=self.agent_id
                    ))
                    
                logger.info(f"🛑 Exit vetoed for {token} - {result['reason']}")
                
        except Exception as e:
            logger.error(f"Veto check error: {e}")
            
        return result
        
    # ============================================
    # EXIT BLOCKER
    # ============================================
    
    async def should_block_exit(self, token: str, exit_data: Dict) -> Dict:
        """
        Determine if an exit should be blocked
        """
        result = {
            'blocked': False,
            'reason': '',
            'conditions_met': []
        }
        
        try:
            # Check Let Winners Run veto first
            veto_result = await self.check_let_winners_run_veto(token, exit_data)
            if veto_result['vetoed']:
                result['blocked'] = True
                result['reason'] = veto_result['reason']
                self.vetoed_exits[token] = veto_result
                return result
            
            # 1. Check ADX
            adx = await self.state_manager.get(f'adx_{token}', 0)
            if adx > self.config['block_conditions']['adx_threshold']:
                result['conditions_met'].append(f'ADX={adx}')
                
            # 2. Check TPS
            tps = await self.state_manager.get(f'tps_{token}', 0)
            if tps >= self.config['block_conditions']['tps_threshold']:
                result['conditions_met'].append(f'TPS={tps}')
                
            # 3. Check higher highs
            if self.config['block_conditions']['higher_highs_required']:
                higher_highs = await self.state_manager.get(f'higher_highs_{token}', False)
                if higher_highs:
                    result['conditions_met'].append('HigherHighs')
                    
            # 4. Check higher lows
            if self.config['block_conditions']['higher_lows_required']:
                higher_lows = await self.state_manager.get(f'higher_lows_{token}', False)
                if higher_lows:
                    result['conditions_met'].append('HigherLows')
                    
            # Block if 2+ conditions met
            if len(result['conditions_met']) >= 2:
                result['blocked'] = True
                result['reason'] = f'Blocked by: {", ".join(result["conditions_met"])}'
                self.blocked_exits[token] = {
                    'time': datetime.now().isoformat(),
                    'conditions': result['conditions_met']
                }
                
        except Exception as e:
            logger.error(f"Exit block check error: {e}")
            
        return result
        
    async def check_blocked_exits(self):
        """Check if blocked exits should be unblocked"""
        for token in list(self.blocked_exits.keys()):
            # Check if conditions have changed
            adx = await self.state_manager.get(f'adx_{token}', 0)
            tps = await self.state_manager.get(f'tps_{token}', 0)
            
            if adx <= 25 or tps < 70:
                # Unblock
                del self.blocked_exits[token]
                logger.info(f"🔓 Exit unblocked for {token}")
                
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_exit_request(self, event: Event):
        """Handle exit requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        exit_data = event.data.get('exit_data', {})
        request_id = event.data.get('request_id')
        
        # Check if exit should be blocked
        block_result = await self.should_block_exit(token, exit_data)
        
        response = Event(
            event_type="exit_request_response",
            data={
                'request_id': request_id,
                'token': token,
                'blocked': block_result['blocked'],
                'reason': block_result['reason'],
                'conditions_met': block_result['conditions_met'],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_position_update(self, event: Event):
        """Handle position updates"""
        if not self.running:
            return
            
        token = event.data.get('token')
        position = event.data.get('position', {})
        
        if token:
            # Check if this is a winner position
            tps = await self.state_manager.get(f'tps_{token}', 0)
            if tps >= 85:
                await self.state_manager.set(f'winner_{token}', True)
            else:
                await self.state_manager.set(f'winner_{token}', False)
                
    async def publish_blocker_status(self):
        """Publish blocker status"""
        status_data = {
            'blocked_exits': len(self.blocked_exits),
            'vetoed_exits': len(self.vetoed_exits),
            'blocked_tokens': list(self.blocked_exits.keys()),
            'vetoed_tokens': list(self.vetoed_exits.keys()),
            'let_winners_run_veto_enabled': self.let_winners_run_veto['enabled'],
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="exit_blocker_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get early exit blocker status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'blocked_exits': len(self.blocked_exits),
            'vetoed_exits': len(self.vetoed_exits),
            'blocked_tokens': list(self.blocked_exits.keys()),
            'vetoed_tokens': list(self.vetoed_exits.keys()),
            'let_winners_run_veto_enabled': self.let_winners_run_veto['enabled'],
            'timestamp': datetime.now().isoformat()
        }
