"""
AlphaEdge Agent 34 – Solver Network Executor
Best-price execution via solver networks
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SolverNetworkExecutor:
    """Solver Network Executor – Best-price execution via solver networks"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "solver_network"
        self.running = False
        
        # Solver state
        self.solvers = {}
        self.solver_responses = {}
        self.execution_history = []
        
        # Solver network parameters
        self.networks = ['Jupiter', '1Inch', 'Paraswap', '0x']
        self.solver_timeout = 10  # seconds
        
    async def start(self):
        """Start the solver network executor"""
        logger.info("Solver Network Executor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("solver_request", self.handle_solver_request)
        await self.event_bus.subscribe("solver_response", self.handle_solver_response)
        await self.event_bus.subscribe("solver_status_request", self.handle_solver_status)
        
        # Start solver cycle
        asyncio.create_task(self.run_solver_cycle())
        
        logger.info("Solver Network Executor running")
        
    async def stop(self):
        """Stop the solver network executor"""
        self.running = False
        logger.info("Solver Network Executor stopped")
        
    async def run_solver_cycle(self):
        """Run regular solver cycle"""
        while self.running:
            try:
                # Update solver status
                await self.update_solver_status()
                
                # Process pending solver responses
                await self.process_solver_responses()
                
                # Publish solver update
                await self.publish_solver_update()
                
            except Exception as e:
                logger.error(f"Solver cycle error: {e}")
                
            await asyncio.sleep(10)  # Every 10 seconds
            
    async def handle_solver_request(self, event: Event):
        """Handle solver requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        order = event.data.get('order', {})
        
        logger.info(f"Solver request: {request_id}")
        
        # Broadcast to solver networks
        await self.broadcast_to_solvers(request_id, order)
        
        # Wait for responses
        responses = await self.collect_responses(request_id)
        
        # Select best response
        best_response = await self.select_best_response(responses)
        
        # Execute best response
        execution_result = await self.execute_solver_order(best_response)
        
        # Send response
        response = Event(
            event_type="solver_result",
            data={
                'request_id': request_id,
                'responses': responses,
                'best_response': best_response,
                'execution_result': execution_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def broadcast_to_solvers(self, request_id: str, order: Dict):
        """Broadcast order to all solver networks"""
        # Prepare broadcast message
        message = {
            'request_id': request_id,
            'order': order,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to each solver network
        for network in self.networks:
            solver_event = Event(
                event_type="solver_broadcast",
                data=message,
                source=self.agent_id,
                target=f"solver_{network}"
            )
            await self.event_bus.publish(solver_event)
            
        logger.info(f"Broadcasted to {len(self.networks)} solvers")
        
    async def collect_responses(self, request_id: str) -> List[Dict]:
        """Collect responses from solver networks"""
        responses = []
        start_time = datetime.now()
        
        # Wait for responses
        while (datetime.now() - start_time).seconds < self.solver_timeout:
            if request_id in self.solver_responses:
                responses = self.solver_responses[request_id]
                break
            await asyncio.sleep(0.1)
            
        # Clean up
        if request_id in self.solver_responses:
            del self.solver_responses[request_id]
            
        return responses
        
    async def select_best_response(self, responses: List[Dict]) -> Dict:
        """Select the best response from solver networks"""
        if not responses:
            return {'error': 'No responses received'}
            
        # Sort by price (best price first)
        sorted_responses = sorted(
            responses,
            key=lambda x: x.get('price', 0)
        )
        
        # Return best response
        best = sorted_responses[0]
        
        # Add selection info
        best['selected'] = True
        best['selection_reason'] = f"Best price: {best.get('price', 0)}"
        
        return best
        
    async def execute_solver_order(self, response: Dict) -> Dict:
        """Execute order through selected solver"""
        if response.get('error'):
            return {
                'status': 'failed',
                'reason': response['error']
            }
            
        # In production, execute through solver
        # For now, simulate execution
        
        return {
            'status': 'executed',
            'solver': response.get('solver', 'unknown'),
            'price': response.get('price', 0),
            'tx_hash': f"tx_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat()
        }
        
    async def handle_solver_response(self, event: Event):
        """Handle solver responses"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        response = event.data.get('response', {})
        solver = event.source
        
        # Store response
        if request_id not in self.solver_responses:
            self.solver_responses[request_id] = []
            
        response['solver'] = solver
        self.solver_responses[request_id].append(response)
        
        # Update solver status
        self.solvers[solver] = {
            'last_response': datetime.now().isoformat(),
            'success_count': self.solvers.get(solver, {}).get('success_count', 0) + 1
        }
        
        logger.info(f"Response received from {solver} for {request_id}")
        
    async def handle_solver_status(self, event: Event):
        """Handle solver status requests"""
        if not self.running:
            return
            
        solver = event.data.get('solver')
        
        if solver:
            status = self.solvers.get(solver, {})
        else:
            status = self.solvers
            
        response = Event(
            event_type="solver_status_response",
            data={
                'solver': solver,
                'status': status,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def update_solver_status(self):
        """Update solver network status"""
        # In production, ping each solver
        # For now, simulate status
        for network in self.networks:
            solver_name = f"solver_{network}"
            if solver_name not in self.solvers:
                self.solvers[solver_name] = {
                    'status': 'active',
                    'last_response': datetime.now().isoformat(),
                    'success_count': 0,
                    'avg_response_time': random.uniform(0.5, 2.0)
                }
                
    async def process_solver_responses(self):
        """Process pending solver responses"""
        # Responses are processed in handle_solver_response
        pass
        
    async def publish_solver_update(self):
        """Publish solver data update"""
        solver_data = {
            'active_solvers': len(self.solvers),
            'solver_status': self.solvers,
            'execution_history': self.execution_history[-5:],
            'total_executions': len(self.execution_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="solver_update",
            data=solver_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get solver network executor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_solvers': len(self.solvers),
            'total_executions': len(self.execution_history),
            'solver_timeout': self.solver_timeout,
            'networks': self.networks,
            'timestamp': datetime.now().isoformat()
        }
