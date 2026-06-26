"""
AlphaEdge Agent 45 – Redundancy Manager
RPC failover (Jito SG→Helius SG→Helius Free→Public)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class RedundancyManager:
    """Redundancy Manager – RPC failover and redundancy management"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "redundancy_manager"
        self.running = False
        
        # RPC endpoints (ordered by priority)
        self.rpc_endpoints = {
            'primary': {
                'url': 'https://jito-sg.rpc.com',
                'status': 'active',
                'latency': 0,
                'priority': 1
            },
            'backup_1': {
                'url': 'https://helius-sg.rpc.com',
                'status': 'standby',
                'latency': 0,
                'priority': 2
            },
            'backup_2': {
                'url': 'https://helius-free.rpc.com',
                'status': 'standby',
                'latency': 0,
                'priority': 3
            },
            'public': {
                'url': 'https://api.mainnet-beta.solana.com',
                'status': 'standby',
                'latency': 0,
                'priority': 4
            }
        }
        
        # Current active endpoint
        self.active_endpoint = 'primary'
        self.failover_history = []
        self.health_checks = []
        
    async def start(self):
        """Start the redundancy manager"""
        logger.info("Redundancy Manager starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("endpoint_request", self.handle_endpoint_request)
        await self.event_bus.subscribe("failover_request", self.handle_failover_request)
        await self.event_bus.subscribe("health_check_request", self.handle_health_check)
        
        # Start redundancy cycle
        asyncio.create_task(self.run_redundancy_cycle())
        
        logger.info("Redundancy Manager running")
        
    async def stop(self):
        """Stop the redundancy manager"""
        self.running = False
        logger.info("Redundancy Manager stopped")
        
    async def run_redundancy_cycle(self):
        """Run regular redundancy cycle"""
        while self.running:
            try:
                # Health check all endpoints
                await self.check_all_endpoints()
                
                # Check if failover needed
                await self.check_failover_needed()
                
                # Update endpoint status
                await self.update_endpoint_status()
                
                # Publish redundancy update
                await self.publish_redundancy_update()
                
            except Exception as e:
                logger.error(f"Redundancy cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_endpoint_request(self, event: Event):
        """Handle endpoint requests"""
        if not self.running:
            return
            
        endpoint_type = event.data.get('type', 'active')
        
        if endpoint_type == 'active':
            endpoint = self.rpc_endpoints[self.active_endpoint]
        else:
            endpoint = self.rpc_endpoints
            
        response = Event(
            event_type="endpoint_response",
            data={
                'type': endpoint_type,
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_failover_request(self, event: Event):
        """Handle failover requests"""
        if not self.running:
            return
            
        target = event.data.get('target')
        reason = event.data.get('reason', 'manual')
        
        if target in self.rpc_endpoints:
            await self.perform_failover(target, reason)
            
    async def handle_health_check(self, event: Event):
        """Handle health check requests"""
        if not self.running:
            return
            
        endpoint = event.data.get('endpoint')
        
        if endpoint:
            health = await self.check_endpoint(endpoint)
        else:
            health = await self.check_all_endpoints()
            
        response = Event(
            event_type="health_check_response",
            data={
                'endpoint': endpoint,
                'health': health,
                'active_endpoint': self.active_endpoint,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_all_endpoints(self) -> Dict:
        """Check health of all endpoints"""
        results = {}
        
        for name, endpoint in self.rpc_endpoints.items():
            health = await self.check_endpoint(name)
            results[name] = health
            
        return results
        
    async def check_endpoint(self, name: str) -> Dict:
        """Check health of a specific endpoint"""
        if name not in self.rpc_endpoints:
            return {'status': 'unknown', 'latency': 0}
            
        endpoint = self.rpc_endpoints[name]
        
        # Simulate health check
        # In production, actually ping the RPC
        await asyncio.sleep(0.05)  # Simulate ping
        
        # Simulate latency
        latency = random.uniform(10, 200)
        endpoint['latency'] = latency
        
        # Simulate failure (5% chance)
        if random.random() < 0.05:
            status = 'failed'
        else:
            status = 'active' if latency < 150 else 'degraded'
            
        endpoint['status'] = status
        
        return {
            'name': name,
            'status': status,
            'latency': latency,
            'timestamp': datetime.now().isoformat()
        }
        
    async def check_failover_needed(self):
        """Check if failover is needed"""
        active = self.rpc_endpoints[self.active_endpoint]
        
        # Check if active endpoint is failed
        if active['status'] == 'failed':
            await self.perform_failover(None, 'active_endpoint_failed')
            
        # Check if active endpoint is degraded
        if active['status'] == 'degraded':
            # Check if there's a better endpoint
            for name, endpoint in sorted(
                self.rpc_endpoints.items(),
                key=lambda x: x[1]['priority']
            ):
                if name != self.active_endpoint and endpoint['status'] == 'active':
                    await self.perform_failover(name, 'better_endpoint_available')
                    break
                    
    async def perform_failover(self, target: Optional[str], reason: str):
        """Perform failover to target endpoint"""
        if not target:
            # Find best available endpoint
            target = await self.find_best_endpoint()
            
        if target and target != self.active_endpoint:
            previous = self.active_endpoint
            
            # Perform failover
            self.active_endpoint = target
            self.rpc_endpoints[previous]['status'] = 'standby'
            self.rpc_endpoints[target]['status'] = 'active'
            
            # Record failover
            self.failover_history.append({
                'from': previous,
                'to': target,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"🔄 Failover: {previous} → {target} ({reason})")
            
            # Publish failover event
            failover_event = Event(
                event_type="failover_completed",
                data={
                    'from': previous,
                    'to': target,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(failover_event)
            
    async def find_best_endpoint(self) -> str:
        """Find best available endpoint"""
        for name, endpoint in sorted(
            self.rpc_endpoints.items(),
            key=lambda x: x[1]['priority']
        ):
            if name != self.active_endpoint and endpoint['status'] in ['active', 'standby']:
                return name
        return None
        
    async def update_endpoint_status(self):
        """Update endpoint status in state"""
        await self.state_manager.set('rpc_endpoints', self.rpc_endpoints)
        await self.state_manager.set('active_rpc_endpoint', self.active_endpoint)
        
    async def publish_redundancy_update(self):
        """Publish redundancy data update"""
        redundancy_data = {
            'active_endpoint': self.active_endpoint,
            'endpoints': self.rpc_endpoints,
            'failover_history': self.failover_history[-5:],
            'total_failovers': len(self.failover_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="redundancy_update",
            data=redundancy_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get redundancy manager status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_endpoint': self.active_endpoint,
            'endpoints': self.rpc_endpoints,
            'failovers': len(self.failover_history),
            'timestamp': datetime.now().isoformat()
        }
