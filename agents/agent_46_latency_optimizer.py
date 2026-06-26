"""
AlphaEdge Agent 46 – Latency Optimizer
Connection pooling, request batching, response caching, RPC ping every 30-60s
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from collections import deque

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class LatencyOptimizer:
    """Latency Optimizer – Optimizes system latency"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "latency_optimizer"
        self.running = False
        
        # Latency metrics
        self.latency_metrics = {}
        self.optimization_history = []
        self.ping_results = deque(maxlen=100)
        
        # Connection pool
        self.connection_pool = {}
        self.pool_size = 10
        
        # Cache
        self.cache = {}
        self.cache_ttl = 5  # seconds
        
        # Batch processing
        self.batch_requests = []
        self.batch_interval = 0.1  # 100ms
        
    async def start(self):
        """Start the latency optimizer"""
        logger.info("Latency Optimizer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("optimization_request", self.handle_optimization_request)
        await self.event_bus.subscribe("batch_request", self.handle_batch_request)
        await self.event_bus.subscribe("ping_request", self.handle_ping_request)
        
        # Start optimization cycle
        asyncio.create_task(self.run_optimization_cycle())
        
        # Start ping cycle
        asyncio.create_task(self.run_ping_cycle())
        
        logger.info("Latency Optimizer running")
        
    async def stop(self):
        """Stop the latency optimizer"""
        self.running = False
        logger.info("Latency Optimizer stopped")
        
    async def run_optimization_cycle(self):
        """Run regular optimization cycle"""
        while self.running:
            try:
                # Optimize connection pool
                await self.optimize_connection_pool()
                
                # Process batch requests
                await self.process_batch_requests()
                
                # Clean cache
                await self.clean_cache()
                
                # Update latency metrics
                await self.update_latency_metrics()
                
                # Publish optimization update
                await self.publish_optimization_update()
                
            except Exception as e:
                logger.error(f"Optimization cycle error: {e}")
                
            await asyncio.sleep(10)  # Every 10 seconds
            
    async def run_ping_cycle(self):
        """Run regular ping cycle"""
        while self.running:
            try:
                # Ping RPC endpoints
                ping_results = await self.ping_rpc_endpoints()
                
                # Store results
                self.ping_results.append({
                    'timestamp': datetime.now().isoformat(),
                    'results': ping_results
                })
                
                # Publish ping results
                await self.publish_ping_results(ping_results)
                
            except Exception as e:
                logger.error(f"Ping cycle error: {e}")
                
            # Random interval between 30-60 seconds
            interval = random.uniform(30, 60)
            await asyncio.sleep(interval)
            
    async def handle_optimization_request(self, event: Event):
        """Handle optimization requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        target = event.data.get('target', 'all')
        
        # Run optimization
        results = await self.run_optimization(target)
        
        response = Event(
            event_type="optimization_response",
            data={
                'request_id': request_id,
                'target': target,
                'results': results,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_batch_request(self, event: Event):
        """Handle batch requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        requests = event.data.get('requests', [])
        
        # Queue for batch processing
        self.batch_requests.append({
            'id': request_id,
            'requests': requests,
            'timestamp': datetime.now().isoformat()
        })
        
    async def handle_ping_request(self, event: Event):
        """Handle ping requests"""
        if not self.running:
            return
            
        target = event.data.get('target', 'all')
        
        if target == 'all':
            results = await self.ping_rpc_endpoints()
        else:
            results = await self.ping_endpoint(target)
            
        response = Event(
            event_type="ping_response",
            data={
                'target': target,
                'results': results,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def optimize_connection_pool(self):
        """Optimize connection pool"""
        # In production, manage actual connections
        # For now, simulate pool management
        
        # Clean stale connections
        current_time = time.time()
        stale_timeout = 60  # seconds
        
        for conn_id, conn in list(self.connection_pool.items()):
            if current_time - conn.get('last_used', current_time) > stale_timeout:
                del self.connection_pool[conn_id]
                
        # Ensure minimum pool size
        while len(self.connection_pool) < self.pool_size:
            conn_id = f"conn_{len(self.connection_pool)}"
            self.connection_pool[conn_id] = {
                'created': current_time,
                'last_used': current_time,
                'status': 'active'
            }
            
        # Update metrics
        await self.state_manager.set('connection_pool_size', len(self.connection_pool))
        
    async def process_batch_requests(self):
        """Process batched requests"""
        if not self.batch_requests:
            return
            
        # Process all queued batch requests
        for batch in self.batch_requests[:10]:  # Process up to 10 batches
            await self.process_single_batch(batch)
            
        # Clear processed batches
        self.batch_requests = []
        
    async def process_single_batch(self, batch: Dict):
        """Process a single batch of requests"""
        logger.info(f"Processing batch: {batch['id']}")
        
        # In production, actually process batch
        # For now, simulate processing
        await asyncio.sleep(0.01)  # Simulate batch processing
        
        # Publish batch results
        batch_event = Event(
            event_type="batch_processed",
            data={
                'batch_id': batch['id'],
                'processed': len(batch['requests']),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(batch_event)
        
    async def clean_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        
        for key, entry in list(self.cache.items()):
            if current_time - entry.get('timestamp', current_time) > self.cache_ttl:
                del self.cache[key]
                
    async def update_latency_metrics(self):
        """Update latency metrics"""
        # Calculate average ping latency
        if self.ping_results:
            recent_pings = list(self.ping_results)[-10:]
            avg_latency = 0
            count = 0
            
            for result in recent_pings:
                for endpoint, data in result.get('results', {}).items():
                    avg_latency += data.get('latency', 0)
                    count += 1
                    
            if count > 0:
                avg_latency /= count
            else:
                avg_latency = 0
                
            self.latency_metrics['avg_rpc_latency'] = avg_latency
            
        # Store in state
        await self.state_manager.set('latency_metrics', self.latency_metrics)
        
    async def ping_rpc_endpoints(self) -> Dict:
        """Ping RPC endpoints"""
        # In production, actually ping RPC
        # For now, simulate ping
        endpoints = ['jito_sg', 'helius_sg', 'helius_free', 'public']
        results = {}
        
        for endpoint in endpoints:
            # Simulate latency
            latency = random.uniform(20, 200)
            results[endpoint] = {
                'status': 'success' if latency < 150 else 'degraded',
                'latency': latency,
                'timestamp': datetime.now().isoformat()
            }
            
        return results
        
    async def ping_endpoint(self, endpoint: str) -> Dict:
        """Ping a specific endpoint"""
        # Similar to ping_rpc_endpoints but for single endpoint
        latency = random.uniform(20, 200)
        
        return {
            endpoint: {
                'status': 'success' if latency < 150 else 'degraded',
                'latency': latency,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    async def run_optimization(self, target: str) -> Dict:
        """Run specific optimizations"""
        results = {}
        
        if target in ['connection_pool', 'all']:
            await self.optimize_connection_pool()
            results['connection_pool'] = 'optimized'
            
        if target in ['cache', 'all']:
            await self.clean_cache()
            results['cache'] = 'cleaned'
            
        if target in ['batching', 'all']:
            await self.process_batch_requests()
            results['batching'] = 'processed'
            
        return results
        
    async def publish_ping_results(self, results: Dict):
        """Publish ping results"""
        ping_event = Event(
            event_type="ping_results",
            data={
                'results': results,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(ping_event)
        
    async def publish_optimization_update(self):
        """Publish optimization data update"""
        optimization_data = {
            'latency_metrics': self.latency_metrics,
            'connection_pool_size': len(self.connection_pool),
            'cache_size': len(self.cache),
            'pending_batches': len(self.batch_requests),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="optimization_update",
            data=optimization_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get latency optimizer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'connection_pool_size': len(self.connection_pool),
            'cache_size': len(self.cache),
            'pending_batches': len(self.batch_requests),
            'ping_results': len(self.ping_results),
            'timestamp': datetime.now().isoformat()
        }
