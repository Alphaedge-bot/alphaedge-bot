"""
AlphaEdge Agent 51 – Sub-Agent Router
Latency optimization, route simple signals to heuristic, complex to LLM
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SubAgentRouter:
    """Sub-Agent Router – Routes signals to appropriate processing"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "sub_router"
        self.running = False
        
        # Router state
        self.routing_history = []
        self.performance_metrics = {
            'heuristic': {'processed': 0, 'avg_time': 0},
            'llm': {'processed': 0, 'avg_time': 0},
            'hybrid': {'processed': 0, 'avg_time': 0}
        }
        
        # Signal complexity thresholds
        self.thresholds = {
            'simple': {'max_tokens': 100, 'max_params': 5},
            'complex': {'min_tokens': 500, 'min_params': 10}
        }
        
    async def start(self):
        """Start the sub-agent router"""
        logger.info("Sub-Agent Router starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("routing_request", self.handle_routing_request)
        await self.event_bus.subscribe("signal_processed", self.handle_signal_processed)
        await self.event_bus.subscribe("router_status_request", self.handle_status_request)
        
        # Start routing cycle
        asyncio.create_task(self.run_routing_cycle())
        
        logger.info("Sub-Agent Router running")
        
    async def stop(self):
        """Stop the sub-agent router"""
        self.running = False
        logger.info("Sub-Agent Router stopped")
        
    async def run_routing_cycle(self):
        """Run regular routing cycle"""
        while self.running:
            try:
                # Update routing metrics
                await self.update_metrics()
                
                # Optimize routing decisions
                await self.optimize_routing()
                
                # Publish routing update
                await self.publish_routing_update()
                
            except Exception as e:
                logger.error(f"Routing cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_routing_request(self, event: Event):
        """Handle routing requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        signal = event.data.get('signal')
        
        logger.info(f"Routing request: {request_id}")
        
        # Determine complexity
        complexity = await self.analyze_complexity(signal)
        
        # Route based on complexity
        if complexity == 'simple':
            route = 'heuristic'
        elif complexity == 'complex':
            route = 'llm'
        else:
            route = 'hybrid'
            
        # Process signal
        result = await self.route_signal(signal, route)
        
        # Send response
        response = Event(
            event_type="routing_response",
            data={
                'request_id': request_id,
                'route': route,
                'complexity': complexity,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_signal_processed(self, event: Event):
        """Handle signal processed events"""
        if not self.running:
            return
            
        signal_id = event.data.get('signal_id')
        route = event.data.get('route')
        processing_time = event.data.get('processing_time', 0)
        
        # Update performance metrics
        if route in self.performance_metrics:
            self.performance_metrics[route]['processed'] += 1
            current_avg = self.performance_metrics[route]['avg_time']
            count = self.performance_metrics[route]['processed']
            self.performance_metrics[route]['avg_time'] = (
                (current_avg * (count - 1) + processing_time) / count
            )
            
    async def handle_status_request(self, event: Event):
        """Handle status requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="router_status_response",
            data={
                'performance_metrics': self.performance_metrics,
                'routing_history': self.routing_history[-10:],
                'thresholds': self.thresholds,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def analyze_complexity(self, signal: Dict) -> str:
        """Analyze signal complexity"""
        # Get signal properties
        tokens = len(str(signal).split())
        params = len(signal.get('params', {}))
        
        # Determine complexity
        if tokens < self.thresholds['simple']['max_tokens'] and params < self.thresholds['simple']['max_params']:
            return 'simple'
        elif tokens > self.thresholds['complex']['min_tokens'] or params > self.thresholds['complex']['min_params']:
            return 'complex'
        else:
            return 'medium'
            
    async def route_signal(self, signal: Dict, route: str) -> Dict:
        """Route signal to appropriate processor"""
        start_time = datetime.now()
        
        if route == 'heuristic':
            result = await self.process_heuristic(signal)
        elif route == 'llm':
            result = await self.process_llm(signal)
        else:
            result = await self.process_hybrid(signal)
            
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Record routing
        self.routing_history.append({
            'signal_id': signal.get('id'),
            'route': route,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update metrics
        self.performance_metrics[route]['processed'] += 1
        
        return result
        
    async def process_heuristic(self, signal: Dict) -> Dict:
        """Process signal with heuristic rules"""
        # Simulate heuristic processing (fast)
        await asyncio.sleep(0.01)  # 10ms
        
        return {
            'status': 'processed',
            'method': 'heuristic',
            'confidence': random.uniform(0.7, 0.85),
            'result': f"Heuristic analysis of {signal.get('type', 'unknown')}"
        }
        
    async def process_llm(self, signal: Dict) -> Dict:
        """Process signal with LLM"""
        # Simulate LLM processing (slower but more accurate)
        await asyncio.sleep(0.1)  # 100ms
        
        return {
            'status': 'processed',
            'method': 'llm',
            'confidence': random.uniform(0.85, 0.95),
            'result': f"LLM analysis of {signal.get('type', 'unknown')}"
        }
        
    async def process_hybrid(self, signal: Dict) -> Dict:
        """Process signal with hybrid approach"""
        # Simulate hybrid processing
        await asyncio.sleep(0.05)  # 50ms
        
        return {
            'status': 'processed',
            'method': 'hybrid',
            'confidence': random.uniform(0.8, 0.9),
            'result': f"Hybrid analysis of {signal.get('type', 'unknown')}"
        }
        
    async def update_metrics(self):
        """Update routing metrics"""
        # Calculate success rates
        for route in self.performance_metrics:
            count = self.performance_metrics[route]['processed']
            if count > 0:
                # Calculate success rate (simulated)
                success_rate = random.uniform(0.8, 0.95)
                self.performance_metrics[route]['success_rate'] = success_rate
                
        # Store in state
        await self.state_manager.set('routing_metrics', self.performance_metrics)
        
    async def optimize_routing(self):
        """Optimize routing decisions"""
        # Check if thresholds need adjustment
        # In production, use performance data to adjust
        if len(self.routing_history) > 100:
            # Analyze routing performance
            llm_success = self.performance_metrics['llm'].get('success_rate', 0)
            heuristic_success = self.performance_metrics['heuristic'].get('success_rate', 0)
            
            # Adjust thresholds if needed
            if llm_success - heuristic_success > 0.1:
                # LLM performs significantly better, lower complexity threshold
                self.thresholds['simple']['max_tokens'] = max(50, self.thresholds['simple']['max_tokens'] - 10)
            elif heuristic_success - llm_success > 0.1:
                # Heuristic performs significantly better, raise complexity threshold
                self.thresholds['simple']['max_tokens'] = min(150, self.thresholds['simple']['max_tokens'] + 10)
                
    async def publish_routing_update(self):
        """Publish routing data update"""
        routing_data = {
            'performance_metrics': self.performance_metrics,
            'routing_history': self.routing_history[-5:],
            'thresholds': self.thresholds,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="routing_update",
            data=routing_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get sub-agent router status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'performance_metrics': self.performance_metrics,
            'routing_history': len(self.routing_history),
            'thresholds': self.thresholds,
            'timestamp': datetime.now().isoformat()
        }
