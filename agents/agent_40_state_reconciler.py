"""
AlphaEdge Agent 40 – State Reconciler
3-way WAL + replay on crash, stuck intent resolver, checkpoint management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class StateReconciler:
    """State Reconciler – 3-way WAL + crash recovery, stuck intent resolution"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "state_reconciler"
        self.running = False
        
        # State reconciliation
        self.checkpoint_chain = []
        self.pending_intents = []
        self.recovery_history = []
        
        # WAL configuration
        self.wal_path = "data/wal"
        self.checkpoint_interval = 300  # 5 minutes
        self.max_checkpoints = 100
        
    async def start(self):
        """Start the state reconciler"""
        logger.info("State Reconciler starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("reconciliation_request", self.handle_reconciliation_request)
        await self.event_bus.subscribe("stuck_intent", self.handle_stuck_intent)
        await self.event_bus.subscribe("checkpoint_request", self.handle_checkpoint_request)
        
        # Start reconciliation cycle
        asyncio.create_task(self.run_reconciliation_cycle())
        
        logger.info("State Reconciler running")
        
    async def stop(self):
        """Stop the state reconciler"""
        self.running = False
        logger.info("State Reconciler stopped")
        
    async def run_reconciliation_cycle(self):
        """Run regular reconciliation cycle"""
        while self.running:
            try:
                # Check for stuck intents
                await self.resolve_stuck_intents()
                
                # Create checkpoint if needed
                await self.create_checkpoint()
                
                # Verify WAL integrity
                await self.verify_wal_integrity()
                
                # Publish reconciliation update
                await self.publish_reconciliation_update()
                
            except Exception as e:
                logger.error(f"Reconciliation cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_reconciliation_request(self, event: Event):
        """Handle reconciliation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        action = event.data.get('action')
        
        logger.info(f"Reconciliation request: {request_id} ({action})")
        
        if action == 'replay':
            result = await self.replay_wal()
        elif action == 'verify':
            result = await self.verify_wal_integrity()
        elif action == 'recover':
            result = await self.recover_from_checkpoint()
        else:
            result = {'status': 'unknown_action'}
            
        response = Event(
            event_type="reconciliation_response",
            data={
                'request_id': request_id,
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_stuck_intent(self, event: Event):
        """Handle stuck intent events"""
        if not self.running:
            return
            
        intent = event.data
        intent_id = intent.get('id')
        
        logger.info(f"Stuck intent detected: {intent_id}")
        
        self.pending_intents.append({
            'id': intent_id,
            'data': intent,
            'detected_at': datetime.now().isoformat(),
            'resolved': False
        })
        
    async def handle_checkpoint_request(self, event: Event):
        """Handle checkpoint requests"""
        if not self.running:
            return
            
        checkpoint_id = event.data.get('checkpoint_id')
        
        if checkpoint_id:
            result = await self.restore_checkpoint(checkpoint_id)
        else:
            result = await self.create_checkpoint()
            
        response = Event(
            event_type="checkpoint_response",
            data={
                'checkpoint_id': checkpoint_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def create_checkpoint(self) -> Dict:
        """Create a new state checkpoint"""
        # Get current state
        state = await self.state_manager.get_state_snapshot()
        
        # Create checkpoint
        checkpoint = {
            'id': f"checkpoint_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'checksum': self.calculate_checksum(state),
            'version': 'V13.0.5'
        }
        
        # Store checkpoint
        self.checkpoint_chain.append(checkpoint)
        if len(self.checkpoint_chain) > self.max_checkpoints:
            self.checkpoint_chain = self.checkpoint_chain[-self.max_checkpoints:]
            
        # Write to WAL
        await self.write_to_wal(checkpoint)
        
        logger.info(f"Checkpoint created: {checkpoint['id']}")
        
        return {
            'status': 'created',
            'checkpoint': checkpoint
        }
        
    async def restore_checkpoint(self, checkpoint_id: str) -> Dict:
        """Restore from a specific checkpoint"""
        # Find checkpoint
        checkpoint = None
        for cp in self.checkpoint_chain:
            if cp['id'] == checkpoint_id:
                checkpoint = cp
                break
                
        if not checkpoint:
            return {'status': 'failed', 'reason': 'Checkpoint not found'}
            
        # Verify checksum
        if self.calculate_checksum(checkpoint['state']) != checkpoint['checksum']:
            return {'status': 'failed', 'reason': 'Checksum mismatch'}
            
        # Restore state
        await self.state_manager.restore_state(checkpoint['state'])
        
        logger.info(f"Checkpoint restored: {checkpoint_id}")
        
        return {
            'status': 'restored',
            'checkpoint': checkpoint
        }
        
    async def replay_wal(self) -> Dict:
        """Replay Write-Ahead Log"""
        # In production, read from WAL file
        # For now, simulate replay
        logger.info("Replaying WAL...")
        
        # Get last checkpoint
        last_checkpoint = self.checkpoint_chain[-1] if self.checkpoint_chain else None
        
        # Replay operations
        operations = await self.state_manager.get_operations_after_checkpoint()
        
        for op in operations:
            await self.apply_operation(op)
            
        return {
            'status': 'replayed',
            'checkpoint': last_checkpoint,
            'operations_replayed': len(operations)
        }
        
    async def apply_operation(self, op: Dict):
        """Apply a single operation"""
        op_type = op.get('type')
        key = op.get('key')
        value = op.get('value')
        
        if op_type == 'set':
            await self.state_manager.set(key, value, persist=False)
        elif op_type == 'delete':
            await self.state_manager.delete(key, persist=False)
        elif op_type == 'update':
            await self.state_manager.update(key, value, persist=False)
            
    async def verify_wal_integrity(self) -> Dict:
        """Verify WAL integrity"""
        # In production, read from WAL file
        # For now, simulate verification
        integrity = True
        issues = []
        
        # Check checkpoint chain
        for i, cp in enumerate(self.checkpoint_chain):
            if i > 0:
                previous = self.checkpoint_chain[i-1]
                # Check timestamp ordering
                if cp['timestamp'] < previous['timestamp']:
                    integrity = False
                    issues.append(f"Checkpoint {cp['id']} has invalid timestamp")
                    
            # Check checksum
            if self.calculate_checksum(cp['state']) != cp['checksum']:
                integrity = False
                issues.append(f"Checkpoint {cp['id']} has invalid checksum")
                
        return {
            'integrity': integrity,
            'issues': issues,
            'checkpoints_checked': len(self.checkpoint_chain)
        }
        
    async def resolve_stuck_intents(self):
        """Resolve stuck intents"""
        for intent in self.pending_intents:
            if not intent['resolved']:
                # Attempt to resolve
                resolved = await self.resolve_intent(intent)
                
                if resolved:
                    intent['resolved'] = True
                    intent['resolved_at'] = datetime.now().isoformat()
                    self.recovery_history.append(intent)
                    
    async def resolve_intent(self, intent: Dict) -> bool:
        """Resolve a single stuck intent"""
        # Check if intent can be retried
        if intent['data'].get('retry_count', 0) < 3:
            # Retry the intent
            retry_event = Event(
                event_type="intent_retry",
                data=intent['data'],
                source=self.agent_id
            )
            await self.event_bus.publish(retry_event)
            return True
        else:
            # Mark as failed
            logger.warning(f"Intent {intent['id']} failed after 3 retries")
            
            # Notify failure
            failure_event = Event(
                event_type="intent_failed",
                data=intent['data'],
                source=self.agent_id
            )
            await self.event_bus.publish(failure_event)
            return False
            
    async def recover_from_checkpoint(self) -> Dict:
        """Recover from latest checkpoint"""
        if not self.checkpoint_chain:
            return {'status': 'failed', 'reason': 'No checkpoints available'}
            
        latest = self.checkpoint_chain[-1]
        return await self.restore_checkpoint(latest['id'])
        
    def calculate_checksum(self, data: Dict) -> str:
        """Calculate checksum of data"""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
        
    async def write_to_wal(self, checkpoint: Dict):
        """Write checkpoint to WAL"""
        # In production, write to file
        # For now, simulate
        logger.info(f"WAL: {checkpoint['id']} written")
        
    async def publish_reconciliation_update(self):
        """Publish reconciliation data update"""
        reconciliation_data = {
            'checkpoints': len(self.checkpoint_chain),
            'pending_intents': len([i for i in self.pending_intents if not i['resolved']]),
            'resolved_intents': len([i for i in self.pending_intents if i['resolved']]),
            'latest_checkpoint': self.checkpoint_chain[-1] if self.checkpoint_chain else None,
            'recovery_history': self.recovery_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="reconciliation_update",
            data=reconciliation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get state reconciler status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'checkpoints': len(self.checkpoint_chain),
            'pending_intents': len([i for i in self.pending_intents if not i['resolved']]),
            'resolved_intents': len([i for i in self.pending_intents if i['resolved']]),
            'recovery_history': len(self.recovery_history),
            'timestamp': datetime.now().isoformat()
        }
