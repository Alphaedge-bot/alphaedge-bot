"""
AlphaEdge Agent 43 – Resource Governor
CPU limit 85%, memory 80%, priority tiers (P0 unlimited, P4 throttle)
"""

import logging
import asyncio
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ResourceGovernor:
    """Resource Governor – Manages system resources and process priorities"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "resource_governor"
        self.running = False
        
        # Resource limits
        self.limits = {
            'cpu': 85,      # Percentage
            'memory': 80,   # Percentage
            'disk': 75,     # Percentage
            'network': 70   # Percentage
        }
        
        # Priority tiers
        self.priority_tiers = {
            'P0': {'label': 'unlimited', 'throttle': 1.0, 'critical': True},
            'P1': {'label': 'high', 'throttle': 0.8, 'critical': True},
            'P2': {'label': 'normal', 'throttle': 0.6, 'critical': False},
            'P3': {'label': 'low', 'throttle': 0.3, 'critical': False},
            'P4': {'label': 'throttled', 'throttle': 0.1, 'critical': False}
        }
        
        # Resource allocation
        self.allocations = {}
        self.throttled_processes = []
        
    async def start(self):
        """Start the resource governor"""
        logger.info("Resource Governor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("resource_request", self.handle_resource_request)
        await self.event_bus.subscribe("priority_update", self.handle_priority_update)
        await self.event_bus.subscribe("throttle_request", self.handle_throttle_request)
        
        # Start governance cycle
        asyncio.create_task(self.run_governance_cycle())
        
        logger.info("Resource Governor running")
        
    async def stop(self):
        """Stop the resource governor"""
        self.running = False
        logger.info("Resource Governor stopped")
        
    async def run_governance_cycle(self):
        """Run regular governance cycle"""
        while self.running:
            try:
                # Monitor resources
                await self.monitor_resources()
                
                # Enforce limits
                await self.enforce_limits()
                
                # Manage priorities
                await self.manage_priorities()
                
                # Publish governance update
                await self.publish_governance_update()
                
            except Exception as e:
                logger.error(f"Governance cycle error: {e}")
                
            await asyncio.sleep(10)  # Every 10 seconds
            
    async def handle_resource_request(self, event: Event):
        """Handle resource requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        resource_type = event.data.get('resource')
        amount = event.data.get('amount', 0)
        
        # Check if resource is available
        available = await self.check_availability(resource_type, amount)
        
        response = Event(
            event_type="resource_response",
            data={
                'request_id': request_id,
                'resource': resource_type,
                'amount': amount,
                'available': available,
                'current_usage': await self.get_current_usage(resource_type),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_priority_update(self, event: Event):
        """Handle priority update requests"""
        if not self.running:
            return
            
        agent = event.data.get('agent')
        tier = event.data.get('tier', 'P2')
        
        if tier in self.priority_tiers:
            self.allocations[agent] = tier
            logger.info(f"Priority updated: {agent} -> {tier}")
            
    async def handle_throttle_request(self, event: Event):
        """Handle throttle requests"""
        if not self.running:
            return
            
        agent = event.data.get('agent')
        action = event.data.get('action', 'throttle')
        
        if action == 'throttle':
            self.throttled_processes.append(agent)
            logger.info(f"Throttling: {agent}")
        elif action == 'restore':
            if agent in self.throttled_processes:
                self.throttled_processes.remove(agent)
                logger.info(f"Restored: {agent}")
                
    async def monitor_resources(self):
        """Monitor system resources"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        await self.state_manager.set('cpu_usage', cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        await self.state_manager.set('memory_usage', memory.percent)
        await self.state_manager.set('memory_available', memory.available / (1024**3))
        
        # Disk
        disk = psutil.disk_usage('/')
        await self.state_manager.set('disk_usage', disk.percent)
        
        # Network (simplified)
        net_io = psutil.net_io_counters()
        await self.state_manager.set('network_sent', net_io.bytes_sent / (1024**2))
        await self.state_manager.set('network_recv', net_io.bytes_recv / (1024**2))
        
    async def enforce_limits(self):
        """Enforce resource limits"""
        # CPU limit
        cpu = await self.state_manager.get('cpu_usage', 0)
        if cpu > self.limits['cpu']:
            logger.warning(f"⚠️ CPU limit exceeded: {cpu}%")
            await self.throttle_high_usage('cpu')
            
        # Memory limit
        memory = await self.state_manager.get('memory_usage', 0)
        if memory > self.limits['memory']:
            logger.warning(f"⚠️ Memory limit exceeded: {memory}%")
            await self.throttle_high_usage('memory')
            
    async def throttle_high_usage(self, resource: str):
        """Throttle processes when resource usage is high"""
        # Identify high-usage processes
        high_usage = []
        
        for agent, tier in self.allocations.items():
            if tier in ['P3', 'P4']:
                high_usage.append(agent)
                
        # Throttle low-priority processes
        for agent in high_usage:
            if agent not in self.throttled_processes:
                self.throttled_processes.append(agent)
                
        # Publish throttle event
        throttle_event = Event(
            event_type="resource_throttle",
            data={
                'resource': resource,
                'throttled_agents': high_usage,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(throttle_event)
        
    async def manage_priorities(self):
        """Manage process priorities"""
        for agent, tier in self.allocations.items():
            priority = self.priority_tiers[tier]
            
            # Update state
            await self.state_manager.set(f'priority_{agent}', tier)
            await self.state_manager.set(f'throttle_{agent}', priority['throttle'])
            
    async def check_availability(self, resource_type: str, amount: float) -> bool:
        """Check if requested resource is available"""
        current = await self.get_current_usage(resource_type)
        
        if resource_type == 'cpu':
            return (current + amount) < self.limits['cpu']
        elif resource_type == 'memory':
            return (current + amount) < self.limits['memory']
        elif resource_type == 'disk':
            return (current + amount) < self.limits['disk']
        else:
            return True
            
    async def get_current_usage(self, resource_type: str) -> float:
        """Get current usage of a resource"""
        if resource_type == 'cpu':
            return await self.state_manager.get('cpu_usage', 0)
        elif resource_type == 'memory':
            return await self.state_manager.get('memory_usage', 0)
        elif resource_type == 'disk':
            return await self.state_manager.get('disk_usage', 0)
        else:
            return 0
            
    async def publish_governance_update(self):
        """Publish governance data update"""
        governance_data = {
            'limits': self.limits,
            'allocations': self.allocations,
            'throttled_processes': self.throttled_processes,
            'cpu_usage': await self.state_manager.get('cpu_usage', 0),
            'memory_usage': await self.state_manager.get('memory_usage', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="governance_update",
            data=governance_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get resource governor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'limits': self.limits,
            'allocations': self.allocations,
            'throttled_processes': len(self.throttled_processes),
            'cpu_usage': await self.state_manager.get('cpu_usage', 0),
            'memory_usage': await self.state_manager.get('memory_usage', 0),
            'timestamp': datetime.now().isoformat()
        }
