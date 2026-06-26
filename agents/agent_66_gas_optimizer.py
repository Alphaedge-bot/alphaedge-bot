"""
AlphaEdge Agent 66 – Gas Optimizer
Dynamic gas reserve (SOL 1/5/10, ETH 0.05/0.1/0.2, BNB 0.5/1/2)
Auto-refill from Wallet 1, 24-hour cooldown per chain
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class GasOptimizer:
    """Gas Optimizer – Dynamic gas reserve management with auto-refill"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "gas_optimizer"
        self.running = False
        
        # Gas state
        self.reserves = {
            'solana': {'current': 0.5, 'minimum': 1.0, 'optimal': 5.0, 'maximum': 10.0},
            'ethereum': {'current': 0.03, 'minimum': 0.05, 'optimal': 0.1, 'maximum': 0.2},
            'bnb': {'current': 0.3, 'minimum': 0.5, 'optimal': 1.0, 'maximum': 2.0}
        }
        
        # Refill tracking
        self.last_refill = {}
        self.refill_history = []
        self.gas_usage_history = []
        
        # Configuration
        self.config = {
            'refill_cooldown_hours': 24,
            'refill_threshold_pct': 0.2,  # 20% of minimum
            'max_refill_per_day': 1,
            'priority_fee_multiplier': 1.0
        }
        
    async def start(self):
        """Start the gas optimizer"""
        logger.info("Gas Optimizer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("gas_status_request", self.handle_gas_status_request)
        await self.event_bus.subscribe("gas_refill_request", self.handle_gas_refill_request)
        await self.event_bus.subscribe("gas_usage_update", self.handle_gas_usage_update)
        
        # Start gas optimization cycle
        asyncio.create_task(self.run_gas_cycle())
        
        logger.info("Gas Optimizer running")
        
    async def stop(self):
        """Stop the gas optimizer"""
        self.running = False
        logger.info("Gas Optimizer stopped")
        
    async def run_gas_cycle(self):
        """Run regular gas optimization cycle"""
        while self.running:
            try:
                # Check all reserves
                await self.check_reserves()
                
                # Update gas status
                await self.update_gas_status()
                
                # Publish gas update
                await self.publish_gas_update()
                
            except Exception as e:
                logger.error(f"Gas cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_gas_status_request(self, event: Event):
        """Handle gas status requests"""
        if not self.running:
            return
            
        chain = event.data.get('chain')
        
        if chain:
            status = self.reserves.get(chain, {})
        else:
            status = self.reserves
            
        response = Event(
            event_type="gas_status_response",
            data={
                'chain': chain,
                'status': status,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_gas_refill_request(self, event: Event):
        """Handle gas refill requests"""
        if not self.running:
            return
            
        chain = event.data.get('chain')
        amount = event.data.get('amount')
        
        if chain:
            result = await self.refill_gas(chain, amount)
        else:
            result = {'status': 'no_chain_specified'}
            
        response = Event(
            event_type="gas_refill_response",
            data={
                'chain': chain,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_gas_usage_update(self, event: Event):
        """Handle gas usage updates"""
        if not self.running:
            return
            
        usage = event.data
        chain = usage.get('chain')
        amount = usage.get('amount', 0)
        
        if chain and chain in self.reserves:
            # Update current reserve
            self.reserves[chain]['current'] = max(0, self.reserves[chain]['current'] - amount)
            
            # Record usage
            self.gas_usage_history.append({
                'chain': chain,
                'amount': amount,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep last 1000 usage records
            if len(self.gas_usage_history) > 1000:
                self.gas_usage_history = self.gas_usage_history[-1000:]
                
    async def check_reserves(self):
        """Check all gas reserves and refill if needed"""
        for chain, reserve in self.reserves.items():
            # Check if refill is needed
            if await self.needs_refill(chain):
                await self.refill_gas(chain)
                
    async def needs_refill(self, chain: str) -> bool:
        """Check if a chain needs refill"""
        if chain not in self.reserves:
            return False
            
        reserve = self.reserves[chain]
        current = reserve['current']
        minimum = reserve['minimum']
        
        # Check if below minimum
        if current < minimum:
            return True
            
        # Check if below threshold of minimum
        if current < minimum * self.config['refill_threshold_pct']:
            return True
            
        return False
        
    async def refill_gas(self, chain: str, amount: Optional[float] = None) -> Dict:
        """Refill gas for a chain"""
        if chain not in self.reserves:
            return {'status': 'failed', 'reason': 'Unknown chain'}
            
        reserve = self.reserves[chain]
        current = reserve['current']
        minimum = reserve['minimum']
        
        # Check cooldown
        if chain in self.last_refill:
            cooldown_remaining = self.last_refill[chain] + timedelta(
                hours=self.config['refill_cooldown_hours']
            )
            if datetime.now() < cooldown_remaining:
                return {
                    'status': 'failed',
                    'reason': 'Cooldown active',
                    'cooldown_until': cooldown_remaining.isoformat()
                }
                
        # Calculate refill amount
        if amount is None:
            # Refill to optimal
            amount = reserve['optimal'] - current
            if amount < 0:
                amount = reserve['minimum'] * 2
                
        # Check if refill is needed
        if amount <= 0:
            return {
                'status': 'failed',
                'reason': 'Insufficient amount'
            }
            
        # In production, execute swap from Wallet 1
        # For now, simulate refill
        logger.info(f"Refilling gas for {chain}: {amount:.4f}")
        
        # Update reserve
        reserve['current'] += amount
        
        # Record refill
        self.last_refill[chain] = datetime.now()
        self.refill_history.append({
            'chain': chain,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'status': 'success',
            'chain': chain,
            'amount_refilled': amount,
            'new_balance': reserve['current'],
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_gas_status(self):
        """Update gas status in state"""
        await self.state_manager.set('gas_reserves', self.reserves)
        await self.state_manager.set('gas_status', {
            'total_gas': sum(r['current'] for r in self.reserves.values()),
            'timestamp': datetime.now().isoformat()
        })
        
    async def publish_gas_update(self):
        """Publish gas data update"""
        gas_data = {
            'reserves': self.reserves,
            'refill_history': self.refill_history[-5:],
            'usage_history': self.gas_usage_history[-5:],
            'last_refill': self.last_refill,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="gas_update",
            data=gas_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get gas optimizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'reserves': self.reserves,
            'total_gas': sum(r['current'] for r in self.reserves.values()),
            'refill_history': len(self.refill_history),
            'last_refill': self.last_refill,
            'timestamp': datetime.now().isoformat()
        }
