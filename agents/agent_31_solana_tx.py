"""
AlphaEdge Agent 31 – Solana Transaction Optimizer
Priority fees (dynamic), CU estimation, leader schedule awareness, retry logic
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SolanaTransactionOptimizer:
    """Solana Transaction Optimizer – Optimizes transaction submission on Solana"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "solana_tx"
        self.running = False
        
        # Transaction state
        self.transaction_queue = []
        self.transaction_history = []
        self.priority_fee_history = []
        
        # Solana parameters
        self.current_priority_fee = 0.0001
        self.compute_unit_price = 0
        self.leader_schedule = []
        
        # Retry parameters
        self.max_retries = 5
        self.retry_delay = 100  # ms
        self.retry_multiplier = 2
        
    async def start(self):
        """Start the Solana transaction optimizer"""
        logger.info("Solana Transaction Optimizer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("solana_tx_request", self.handle_tx_request)
        await self.event_bus.subscribe("tx_status_request", self.handle_tx_status)
        await self.event_bus.subscribe("priority_fee_request", self.handle_priority_fee_request)
        
        # Start optimization cycle
        asyncio.create_task(self.run_optimization_cycle())
        
        logger.info("Solana Transaction Optimizer running")
        
    async def stop(self):
        """Stop the Solana transaction optimizer"""
        self.running = False
        logger.info("Solana Transaction Optimizer stopped")
        
    async def run_optimization_cycle(self):
        """Run regular optimization cycle"""
        while self.running:
            try:
                # Update priority fee
                await self.update_priority_fee()
                
                # Update leader schedule
                await self.update_leader_schedule()
                
                # Process queued transactions
                await self.process_transaction_queue()
                
                # Publish optimizer update
                await self.publish_optimizer_update()
                
            except Exception as e:
                logger.error(f"Optimization cycle error: {e}")
                
            await asyncio.sleep(5)  # Every 5 seconds
            
    async def handle_tx_request(self, event: Event):
        """Handle transaction requests"""
        if not self.running:
            return
            
        tx_data = event.data.get('transaction')
        tx_id = tx_data.get('id', f"tx_{datetime.now().timestamp()}")
        
        logger.info(f"Transaction request: {tx_id}")
        
        # Optimize transaction
        optimized_tx = await self.optimize_transaction(tx_data)
        
        # Queue for submission
        self.transaction_queue.append({
            'id': tx_id,
            'transaction': optimized_tx,
            'status': 'queued',
            'retries': 0,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send response
        response = Event(
            event_type="solana_tx_response",
            data={
                'tx_id': tx_id,
                'status': 'queued',
                'optimized_tx': optimized_tx,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def optimize_transaction(self, tx: Dict) -> Dict:
        """Optimize a Solana transaction"""
        optimized = tx.copy()
        
        # Calculate optimal priority fee
        priority_fee = await self.calculate_priority_fee(tx)
        optimized['priority_fee'] = priority_fee
        
        # Calculate compute units
        compute_units = await self.estimate_compute_units(tx)
        optimized['compute_units'] = compute_units
        
        # Set compute unit price
        optimized['compute_unit_price'] = priority_fee * 1000000  # Micro-lamports
        
        # Add retry logic
        optimized['max_retries'] = self.max_retries
        optimized['retry_delay'] = self.retry_delay
        
        return optimized
        
    async def calculate_priority_fee(self, tx: Dict) -> float:
        """Calculate optimal priority fee"""
        # Base fee
        base_fee = 0.0001
        
        # Network congestion multiplier
        congestion = await self.get_network_congestion()
        congestion_multiplier = 1 + (congestion * 2)
        
        # Transaction urgency
        urgency = tx.get('urgency', 'normal')
        urgency_multipliers = {
            'low': 1.0,
            'normal': 1.5,
            'high': 2.5,
            'critical': 5.0
        }
        urgency_mult = urgency_multipliers.get(urgency, 1.5)
        
        # Compute final fee
        fee = base_fee * congestion_multiplier * urgency_mult
        
        # Cap at reasonable limit
        fee = min(fee, 0.01)  # Max 0.01 SOL
        
        # Store for history
        self.priority_fee_history.append({
            'fee': fee,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.priority_fee_history) > 100:
            self.priority_fee_history.pop(0)
            
        return fee
        
    async def estimate_compute_units(self, tx: Dict) -> int:
        """Estimate compute units for a transaction"""
        # Base compute units
        base_units = 200000
        
        # Additional units based on complexity
        complexity = tx.get('complexity', 'low')
        complexity_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }
        complexity_mult = complexity_multipliers.get(complexity, 1.0)
        
        return int(base_units * complexity_mult)
        
    async def get_network_congestion(self) -> float:
        """Get current network congestion (0-1)"""
        # In production, fetch from Solana RPC
        # For now, simulate congestion
        return random.uniform(0.1, 0.9)
        
    async def update_priority_fee(self):
        """Update current priority fee"""
        # Calculate fee based on congestion
        congestion = await self.get_network_congestion()
        base_fee = 0.0001
        self.current_priority_fee = base_fee * (1 + congestion * 3)
        
        await self.state_manager.set('current_priority_fee', self.current_priority_fee)
        
    async def update_leader_schedule(self):
        """Update Solana leader schedule"""
        # In production, fetch from Solana RPC
        # For now, simulate schedule
        self.leader_schedule = [
            {'slot': i, 'leader': f'leader_{i%5}'}
            for i in range(10)
        ]
        
        await self.state_manager.set('leader_schedule', self.leader_schedule)
        
    async def process_transaction_queue(self):
        """Process queued transactions"""
        for tx_entry in self.transaction_queue[:10]:  # Process up to 10
            if tx_entry['status'] != 'queued':
                continue
                
            # Submit transaction
            result = await self.submit_transaction(tx_entry)
            
            if result['status'] == 'success':
                tx_entry['status'] = 'confirmed'
                logger.info(f"Transaction {tx_entry['id']} confirmed")
            else:
                tx_entry['retries'] += 1
                if tx_entry['retries'] >= self.max_retries:
                    tx_entry['status'] = 'failed'
                    logger.warning(f"Transaction {tx_entry['id']} failed after {self.max_retries} retries")
                else:
                    # Retry with backoff
                    delay = self.retry_delay * (self.retry_multiplier ** tx_entry['retries'])
                    tx_entry['status'] = 'retrying'
                    await asyncio.sleep(delay / 1000)
                    
            # Move to history
            self.transaction_history.append(tx_entry)
            if len(self.transaction_history) > 100:
                self.transaction_history.pop(0)
                
    async def submit_transaction(self, tx_entry: Dict) -> Dict:
        """Submit a transaction to the network"""
        # In production, submit to Solana RPC
        # For now, simulate submission
        
        # Simulate success rate based on priority fee
        fee = tx_entry['transaction'].get('priority_fee', 0.0001)
        success_rate = min(0.95, 0.5 + (fee * 50))
        
        if random.random() < success_rate:
            return {
                'status': 'success',
                'signature': f"sig_{datetime.now().timestamp()}",
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'failed',
                'error': 'Simulated network error',
                'timestamp': datetime.now().isoformat()
            }
            
    async def handle_tx_status(self, event: Event):
        """Handle transaction status requests"""
        if not self.running:
            return
            
        tx_id = event.data.get('tx_id')
        
        # Find transaction
        tx_entry = None
        for entry in self.transaction_history:
            if entry['id'] == tx_id:
                tx_entry = entry
                break
                
        if not tx_entry:
            for entry in self.transaction_queue:
                if entry['id'] == tx_id:
                    tx_entry = entry
                    break
                    
        response = Event(
            event_type="tx_status_response",
            data={
                'tx_id': tx_id,
                'status': tx_entry['status'] if tx_entry else 'not_found',
                'entry': tx_entry,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_priority_fee_request(self, event: Event):
        """Handle priority fee requests"""
        if not self.running:
            return
            
        tx_urgency = event.data.get('urgency', 'normal')
        
        fee = await self.calculate_priority_fee({'urgency': tx_urgency})
        
        response = Event(
            event_type="priority_fee_response",
            data={
                'priority_fee': fee,
                'urgency': tx_urgency,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_optimizer_update(self):
        """Publish optimizer data update"""
        optimizer_data = {
            'current_priority_fee': self.current_priority_fee,
            'queue_size': len(self.transaction_queue),
            'pending_transactions': len([t for t in self.transaction_queue if t['status'] == 'queued']),
            'completed_transactions': len(self.transaction_history),
            'leader_schedule': self.leader_schedule[:5],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="solana_optimizer_update",
            data=optimizer_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get Solana transaction optimizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'queue_size': len(self.transaction_queue),
            'pending_transactions': len([t for t in self.transaction_queue if t['status'] == 'queued']),
            'completed_transactions': len(self.transaction_history),
            'current_priority_fee': self.current_priority_fee,
            'max_retries': self.max_retries,
            'timestamp': datetime.now().isoformat()
        }
