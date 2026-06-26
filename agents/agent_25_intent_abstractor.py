"""
AlphaEdge Agent 25 – Intent Abstractor
Convert swaps to intents, broadcast to solver networks (Jupiter)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class IntentAbstractor:
    """Intent Abstractor – Converts swap requests to intents for solver networks"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "intent_abstractor"
        self.running = False
        
        # Intent state
        self.active_intents = {}
        self.completed_intents = []
        self.pending_intents = []
        
        # Solver networks
        self.solver_networks = ['Jupiter', 'Raydium', 'Orca']
        self.solvers = ['solver1', 'solver2', 'solver3']
        
    async def start(self):
        """Start the intent abstractor"""
        logger.info("Intent Abstractor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("swap_request", self.handle_swap_request)
        await self.event_bus.subscribe("intent_response", self.handle_intent_response)
        await self.event_bus.subscribe("intent_status_request", self.handle_intent_status)
        
        # Start intent processing
        asyncio.create_task(self.run_intent_cycle())
        
        logger.info("Intent Abstractor running")
        
    async def stop(self):
        """Stop the intent abstractor"""
        self.running = False
        logger.info("Intent Abstractor stopped")
        
    async def run_intent_cycle(self):
        """Run regular intent processing"""
        while self.running:
            try:
                # Process pending intents
                await self.process_pending_intents()
                
                # Check expired intents
                await self.check_expired_intents()
                
                # Publish intent update
                await self.publish_intent_update()
                
            except Exception as e:
                logger.error(f"Intent cycle error: {e}")
                
            await asyncio.sleep(5)  # Every 5 seconds
            
    async def handle_swap_request(self, event: Event):
        """Handle swap requests"""
        if not self.running:
            return
            
        swap_data = event.data.get('swap_data', {})
        request_id = event.data.get('request_id', str(uuid.uuid4()))
        
        logger.info(f"Swap request received: {request_id}")
        
        # Create intent
        intent = await self.create_intent(request_id, swap_data)
        
        # Store intent
        self.active_intents[intent['id']] = intent
        
        # Broadcast to solver networks
        await self.broadcast_to_solvers(intent)
        
        # Send response
        response = Event(
            event_type="intent_created",
            data={
                'intent_id': intent['id'],
                'status': 'broadcasting',
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def create_intent(self, request_id: str, swap_data: Dict) -> Dict:
        """Create an intent from swap data"""
        intent = {
            'id': f"intent_{datetime.now().timestamp()}_{request_id}",
            'request_id': request_id,
            'from_token': swap_data.get('from_token'),
            'to_token': swap_data.get('to_token'),
            'amount': swap_data.get('amount'),
            'slippage': swap_data.get('slippage', 0.01),
            'deadline': datetime.now().timestamp() + 60,  # 60 seconds
            'status': 'pending',
            'solver_responses': [],
            'best_solver': None,
            'best_price': None,
            'created_at': datetime.now().isoformat()
        }
        
        return intent
        
    async def broadcast_to_solvers(self, intent: Dict):
        """Broadcast intent to solver networks"""
        logger.info(f"Broadcasting intent {intent['id']} to solvers")
        
        # Create broadcast message
        message = {
            'intent_id': intent['id'],
            'from_token': intent['from_token'],
            'to_token': intent['to_token'],
            'amount': intent['amount'],
            'deadline': intent['deadline']
        }
        
        # Send to each solver
        for solver in self.solvers:
            solver_event = Event(
                event_type="intent_broadcast",
                data=message,
                source=self.agent_id,
                target=solver
            )
            await self.event_bus.publish(solver_event)
            
        # Add to pending
        self.pending_intents.append(intent['id'])
        
    async def handle_intent_response(self, event: Event):
        """Handle responses from solvers"""
        if not self.running:
            return
            
        intent_id = event.data.get('intent_id')
        solver = event.source
        price = event.data.get('price')
        quote = event.data.get('quote')
        
        logger.info(f"Response received for intent {intent_id} from {solver}")
        
        # Find intent
        intent = self.active_intents.get(intent_id)
        if not intent:
            logger.warning(f"Intent {intent_id} not found")
            return
            
        # Record response
        response = {
            'solver': solver,
            'price': price,
            'quote': quote,
            'timestamp': datetime.now().isoformat()
        }
        intent['solver_responses'].append(response)
        
        # Update best solver
        if intent['best_price'] is None or price < intent['best_price']:
            intent['best_price'] = price
            intent['best_solver'] = solver
            
        # Check if we have enough responses to decide
        if len(intent['solver_responses']) >= len(self.solvers):
            await self.finalize_intent(intent_id)
            
    async def finalize_intent(self, intent_id: str):
        """Finalize an intent with best solver"""
        intent = self.active_intents.get(intent_id)
        if not intent:
            return
            
        # Update status
        intent['status'] = 'finalized'
        
        # Remove from pending
        if intent_id in self.pending_intents:
            self.pending_intents.remove(intent_id)
            
        # Move to completed
        self.completed_intents.append(intent)
        
        # Notify best solver
        if intent['best_solver']:
            execution_event = Event(
                event_type="intent_execution",
                data={
                    'intent_id': intent_id,
                    'solver': intent['best_solver'],
                    'price': intent['best_price'],
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id,
                target=intent['best_solver']
            )
            await self.event_bus.publish(execution_event)
            
        logger.info(f"Intent {intent_id} finalized with {intent['best_solver']}")
        
    async def process_pending_intents(self):
        """Process pending intents"""
        for intent_id in self.pending_intents[:10]:
            intent = self.active_intents.get(intent_id)
            if intent:
                # Check if deadline approaching
                current_time = datetime.now().timestamp()
                if current_time > intent['deadline'] - 10:  # 10 seconds before deadline
                    # Force finalization
                    await self.finalize_intent(intent_id)
                    
    async def check_expired_intents(self):
        """Check for expired intents"""
        current_time = datetime.now().timestamp()
        
        for intent_id, intent in list(self.active_intents.items()):
            if current_time > intent['deadline']:
                # Intent expired
                intent['status'] = 'expired'
                self.completed_intents.append(intent)
                del self.active_intents[intent_id]
                
                if intent_id in self.pending_intents:
                    self.pending_intents.remove(intent_id)
                    
                logger.warning(f"Intent {intent_id} expired")
                
    async def handle_intent_status(self, event: Event):
        """Handle intent status requests"""
        if not self.running:
            return
            
        intent_id = event.data.get('intent_id')
        
        # Find intent
        intent = self.active_intents.get(intent_id)
        if not intent:
            # Check completed
            for completed in self.completed_intents:
                if completed['id'] == intent_id:
                    intent = completed
                    break
                    
        response = Event(
            event_type="intent_status_response",
            data={
                'intent_id': intent_id,
                'intent': intent,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_intent_update(self):
        """Publish intent data update"""
        intent_data = {
            'active_intents': len(self.active_intents),
            'pending_intents': len(self.pending_intents),
            'completed_intents': len(self.completed_intents),
            'recent_intents': self.completed_intents[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="intent_update",
            data=intent_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get intent abstractor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_intents': len(self.active_intents),
            'pending_intents': len(self.pending_intents),
            'completed_intents': len(self.completed_intents),
            'solvers': self.solvers,
            'timestamp': datetime.now().isoformat()
        }
