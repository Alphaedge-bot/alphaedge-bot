"""
AlphaEdge Agent 01 – Coordinator (Event Bus Master)
Day-to-day agent coordination via event bus
Task prioritization, resource allocation, execute CEO decisions
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import heapq

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Event Bus Master – Coordinates all agent activities"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "coordinator"
        self.running = False
        self.task_queue = []
        self.active_agents = {}
        self.agent_priorities = {}
        self.task_counter = 0
        
    async def start(self):
        """Start the coordinator agent"""
        logger.info("Coordinator Agent starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("task_request", self.handle_task_request)
        await self.event_bus.subscribe("task_complete", self.handle_task_complete)
        await self.event_bus.subscribe("agent_status", self.handle_agent_status)
        await self.event_bus.subscribe("executive_order", self.handle_executive_order)
        await self.event_bus.subscribe("emergency_stop", self.handle_emergency_stop)
        
        # Start task processor
        asyncio.create_task(self.process_tasks())
        
        logger.info("Coordinator Agent running")
        
    async def stop(self):
        """Stop the coordinator agent"""
        self.running = False
        logger.info("Coordinator Agent stopped")
        
    async def handle_task_request(self, event: Event):
        """Handle task requests from agents"""
        if not self.running:
            return
            
        task = event.data.get('task', {})
        requester = event.source
        priority = task.get('priority', 5)
        
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        # Add to priority queue (negative priority for max-heap)
        heapq.heappush(self.task_queue, (
            -priority,  # Higher priority = smaller number
            self.task_counter,
            {
                'id': task_id,
                'task': task,
                'requester': requester,
                'priority': priority,
                'submitted': datetime.now().isoformat()
            }
        ))
        
        logger.info(f"Task {task_id} queued (priority: {priority})")
        
    async def process_tasks(self):
        """Process tasks from the priority queue"""
        while self.running:
            if self.task_queue:
                # Get highest priority task
                _, _, task_data = heapq.heappop(self.task_queue)
                
                # Find available agent
                agent = await self.find_available_agent(task_data['task'])
                
                if agent:
                    # Assign task to agent
                    assignment = Event(
                        event_type="task_assignment",
                        data={
                            'task_id': task_data['id'],
                            'task': task_data['task'],
                            'assigned_to': agent,
                            'timestamp': datetime.now().isoformat()
                        },
                        source=self.agent_id,
                        target=agent
                    )
                    await self.event_bus.publish(assignment)
                    logger.info(f"Task {task_data['id']} assigned to {agent}")
                else:
                    # No agent available, re-queue with lower priority
                    logger.warning(f"No agent available for task {task_data['id']}, re-queuing")
                    heapq.heappush(self.task_queue, (
                        -task_data['priority'] + 1,  # Decrease priority
                        self.task_counter,
                        task_data
                    ))
                    
            await asyncio.sleep(0.1)
            
    async def find_available_agent(self, task: Dict[str, Any]) -> Optional[str]:
        """Find an available agent for a task"""
        # Check agent availability
        for agent_id, status in self.active_agents.items():
            if status.get('busy', False):
                continue
                
            # Check if agent can handle task type
            capabilities = status.get('capabilities', [])
            task_type = task.get('type', 'general')
            
            if task_type in capabilities or 'general' in capabilities:
                return agent_id
                
        return None
        
    async def handle_task_complete(self, event: Event):
        """Handle task completion notifications"""
        if not self.running:
            return
            
        task_id = event.data.get('task_id')
        agent = event.source
        result = event.data.get('result')
        
        logger.info(f"Task {task_id} completed by {agent}")
        
        # Update agent status
        if agent in self.active_agents:
            self.active_agents[agent]['busy'] = False
            self.active_agents[agent]['last_task'] = task_id
            
    async def handle_agent_status(self, event: Event):
        """Handle agent status updates"""
        if not self.running:
            return
            
        agent_id = event.data.get('agent_id')
        status = event.data.get('status', {})
        
        self.active_agents[agent_id] = status
        logger.debug(f"Agent {agent_id} status updated")
        
    async def handle_executive_order(self, event: Event):
        """Handle executive orders from CEO"""
        if not self.running:
            return
            
        order = event.data.get('order')
        target = event.data.get('target')
        
        if target:
            # Direct order to specific agent
            order_event = Event(
                event_type="executive_order",
                data={'order': order},
                source=self.agent_id,
                target=target
            )
            await self.event_bus.publish(order_event)
            logger.info(f"Executive order sent to {target}")
        else:
            # Broadcast to all agents
            order_event = Event(
                event_type="executive_order",
                data={'order': order},
                source=self.agent_id
            )
            await self.event_bus.publish(order_event)
            logger.info("Executive order broadcast to all agents")
            
    async def handle_emergency_stop(self, event: Event):
        """Handle emergency stop command"""
        if not self.running:
            return
            
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")
        
        # Clear task queue
        self.task_queue = []
        
        # Broadcast emergency stop
        stop_event = Event(
            event_type="emergency_stop",
            data={
                'reason': event.data.get('reason', 'CEO override'),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(stop_event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'tasks_in_queue': len(self.task_queue),
            'active_agents': len(self.active_agents),
            'total_tasks_processed': self.task_counter,
            'timestamp': datetime.now().isoformat()
      }
