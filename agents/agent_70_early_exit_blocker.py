"""
AlphaEdge Agent 70 – Early Exit Blocker
Block premature exits (ADX>40 block, TPS≥82 block, higher highs intact)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class EarlyExitBlocker:
    """Early Exit Blocker – Prevents premature exits based on conditions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "early_exit_blocker"
        self.running = False
        
        # Block state
        self.blocked_exits = []
        self.exit_attempts = []
        
        # Block conditions
        self.config = {
            'adx_threshold': 40,
            'tps_threshold': 82,
            'higher_highs_required': True,
            'min_higher_highs': 2,
            'min_holding_period': 3600  # 1 hour
        }
        
    async def start(self):
        """Start the early exit blocker"""
        logger.info("Early Exit Blocker starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("exit_check", self.handle_exit_check)
        await self.event_bus.subscribe("exit_request", self.handle_exit_request)
        await self.event_bus.subscribe("block_status_request", self.handle_block_status)
        
        # Start blocker cycle
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
                # Update exit attempts
                await self.update_exit_attempts()
                
                # Clean old blocks
                await self.clean_old_blocks()
                
                # Publish blocker update
                await self.publish_blocker_update()
                
            except Exception as e:
                logger.error(f"Blocker cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_exit_check(self, event: Event):
        """Handle exit check requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        exit_data = event.data.get('exit_data', {})
        
        # Check if exit should be blocked
        result = await self.check_exit(token, exit_data)
        
        response = Event(
            event_type="exit_check_response",
            data={
                'token': token,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_exit_request(self, event: Event):
        """Handle exit requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        exit_data = event.data.get('exit_data', {})
        
        # Record attempt
        self.exit_attempts.append({
            'token': token,
            'exit_data': exit_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check if exit should be blocked
        result = await self.check_exit(token, exit_data)
        
        if result['blocked']:
            # Block the exit
            self.blocked_exits.append({
                'token': token,
                'exit_data': exit_data,
                'reason': result['reason'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Send block response
            response = Event(
                event_type="exit_blocked",
                data={
                    'token': token,
                    'reason': result['reason'],
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id,
                target=event.source
            )
            await self.event_bus.publish(response)
            
            logger.info(f"Exit blocked for {token}: {result['reason']}")
            
    async def handle_block_status(self, event: Event):
        """Handle block status requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        
        if token:
            blocks = [b for b in self.blocked_exits if b['token'] == token]
        else:
            blocks = self.blocked_exits
            
        response = Event(
            event_type="block_status_response",
            data={
                'token': token,
                'blocks': blocks[-10:],
                'total_blocks': len(blocks),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_exit(self, token: str, exit_data: Dict) -> Dict:
        """Check if exit should be blocked"""
        reasons = []
        
        # Get current position data
        position = await self.state_manager.get(f'position_{token}', {})
        
        if not position:
            return {'blocked': False, 'reason': 'No position found'}
            
        # Check ADX
        adx = exit_data.get('adx', 0)
        if adx > self.config['adx_threshold']:
            reasons.append(f"ADX {adx} > {self.config['adx_threshold']}")
            
        # Check TPS
        tps = exit_data.get('tps', 0)
        if tps >= self.config['tps_threshold']:
            reasons.append(f"TPS {tps} >= {self.config['tps_threshold']}")
            
        # Check higher highs
        if self.config['higher_highs_required']:
            higher_highs = exit_data.get('higher_highs', 0)
            if higher_highs >= self.config['min_higher_highs']:
                reasons.append(f"Higher highs intact ({higher_highs})")
                
        # Check holding period
        entry_time = position.get('entry_time')
        if entry_time:
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                holding_seconds = (datetime.now() - entry_dt).total_seconds()
                if holding_seconds < self.config['min_holding_period']:
                    reasons.append(f"Holding period too short ({holding_seconds:.0f}s)")
            except:
                pass
                
        # Check volume trend
        volume_trend = exit_data.get('volume_trend', 'stable')
        if volume_trend == 'increasing':
            reasons.append("Volume trend increasing")
            
        # Determine if blocked
        blocked = len(reasons) > 0
        
        return {
            'blocked': blocked,
            'reason': '; '.join(reasons) if blocked else 'No blocking conditions met',
            'check_time': datetime.now().isoformat()
        }
        
    async def update_exit_attempts(self):
        """Update exit attempts"""
        # Keep last 1000 attempts
        if len(self.exit_attempts) > 1000:
            self.exit_attempts = self.exit_attempts[-1000:]
            
    async def clean_old_blocks(self):
        """Clean old block records"""
        # Keep last 500 blocks
        if len(self.blocked_exits) > 500:
            self.blocked_exits = self.blocked_exits[-500:]
            
    async def publish_blocker_update(self):
        """Publish blocker data update"""
        blocker_data = {
            'blocked_exits': self.blocked_exits[-5:],
            'exit_attempts': len(self.exit_attempts),
            'total_blocks': len(self.blocked_exits),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="early_exit_blocker_update",
            data=blocker_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get early exit blocker status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'exit_attempts': len(self.exit_attempts),
            'blocked_exits': len(self.blocked_exits),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
