"""
AlphaEdge Agent 42 – Health Monitor
24/7 surveillance (CPU, RAM, disk, latency, RPC latency), health score 0-100
"""

import logging
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health Monitor – 24/7 system health surveillance"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "health_monitor"
        self.running = False
        
        # Health state
        self.health_score = 100
        self.metrics = {}
        self.history = []
        self.alerts = []
        
        # Thresholds
        self.thresholds = {
            'cpu': 85,
            'memory': 85,
            'disk': 80,
            'latency': 500,  # ms
            'rpc_latency': 1000  # ms
        }
        
    async def start(self):
        """Start the health monitor"""
        logger.info("Health Monitor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("health_request", self.handle_health_request)
        await self.event_bus.subscribe("metric_update", self.handle_metric_update)
        await self.event_bus.subscribe("health_status_request", self.handle_health_status)
        
        # Start health cycle
        asyncio.create_task(self.run_health_cycle())
        
        logger.info("Health Monitor running")
        
    async def stop(self):
        """Stop the health monitor"""
        self.running = False
        logger.info("Health Monitor stopped")
        
    async def run_health_cycle(self):
        """Run regular health monitoring cycle"""
        while self.running:
            try:
                # Collect metrics
                await self.collect_metrics()
                
                # Calculate health score
                await self.calculate_health_score()
                
                # Check for alerts
                await self.check_alerts()
                
                # Publish health update
                await self.publish_health_update()
                
            except Exception as e:
                logger.error(f"Health cycle error: {e}")
                
            await asyncio.sleep(10)  # Every 10 seconds
            
    async def handle_health_request(self, event: Event):
        """Handle health requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="health_response",
            data={
                'health_score': self.health_score,
                'metrics': self.metrics,
                'alerts': self.alerts[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_metric_update(self, event: Event):
        """Handle metric updates"""
        if not self.running:
            return
            
        metric = event.data
        self.metrics.update(metric)
        
    async def handle_health_status(self, event: Event):
        """Handle health status requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="health_status_response",
            data={
                'health_score': self.health_score,
                'metrics': self.metrics,
                'history': self.history[-10:],
                'alerts': self.alerts[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def collect_metrics(self):
        """Collect system metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics['cpu'] = cpu_percent
        
        # Memory
        memory = psutil.virtual_memory()
        self.metrics['memory'] = memory.percent
        self.metrics['memory_used'] = memory.used / (1024**3)  # GB
        self.metrics['memory_total'] = memory.total / (1024**3)  # GB
        
        # Disk
        disk = psutil.disk_usage('/')
        self.metrics['disk'] = disk.percent
        self.metrics['disk_used'] = disk.used / (1024**3)  # GB
        self.metrics['disk_total'] = disk.total / (1024**3)  # GB
        
        # Uptime
        self.metrics['uptime'] = time.time() - psutil.boot_time()
        
        # RPC latency (simulated)
        rpc_latency = await self.measure_rpc_latency()
        self.metrics['rpc_latency'] = rpc_latency
        
        # Store history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.copy()
        })
        if len(self.history) > 100:
            self.history = self.history[-100:]
            
        # Store in state
        await self.state_manager.set('system_metrics', self.metrics)
        
    async def measure_rpc_latency(self) -> float:
        """Measure RPC latency"""
        # In production, ping actual RPC endpoint
        # For now, simulate latency
        import random
        return random.uniform(50, 1500)  # ms
        
    async def calculate_health_score(self):
        """Calculate overall health score (0-100)"""
        score = 100
        penalties = []
        
        # CPU penalty
        cpu = self.metrics.get('cpu', 0)
        if cpu > self.thresholds['cpu']:
            penalty = (cpu - self.thresholds['cpu']) / (100 - self.thresholds['cpu']) * 40
            penalties.append(('cpu', penalty))
            
        # Memory penalty
        memory = self.metrics.get('memory', 0)
        if memory > self.thresholds['memory']:
            penalty = (memory - self.thresholds['memory']) / (100 - self.thresholds['memory']) * 30
            penalties.append(('memory', penalty))
            
        # Disk penalty
        disk = self.metrics.get('disk', 0)
        if disk > self.thresholds['disk']:
            penalty = (disk - self.thresholds['disk']) / (100 - self.thresholds['disk']) * 20
            penalties.append(('disk', penalty))
            
        # RPC latency penalty
        rpc_latency = self.metrics.get('rpc_latency', 0)
        if rpc_latency > self.thresholds['rpc_latency']:
            penalty = (rpc_latency - self.thresholds['rpc_latency']) / (5000) * 10
            penalties.append(('rpc_latency', penalty))
            
        # Apply penalties
        total_penalty = sum(p for _, p in penalties)
        self.health_score = max(0, 100 - total_penalty)
        
        # Store in state
        await self.state_manager.set('health_score', self.health_score)
        
    async def check_alerts(self):
        """Check for health alerts"""
        alerts = []
        
        # CPU alert
        cpu = self.metrics.get('cpu', 0)
        if cpu > self.thresholds['cpu']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning' if cpu < 95 else 'critical',
                'value': cpu,
                'threshold': self.thresholds['cpu']
            })
            
        # Memory alert
        memory = self.metrics.get('memory', 0)
        if memory > self.thresholds['memory']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning' if memory < 95 else 'critical',
                'value': memory,
                'threshold': self.thresholds['memory']
            })
            
        # RPC latency alert
        rpc_latency = self.metrics.get('rpc_latency', 0)
        if rpc_latency > self.thresholds['rpc_latency']:
            alerts.append({
                'type': 'rpc_latency_high',
                'severity': 'warning' if rpc_latency < 3000 else 'critical',
                'value': rpc_latency,
                'threshold': self.thresholds['rpc_latency']
            })
            
        # Health score alert
        if self.health_score < 50:
            alerts.append({
                'type': 'health_score_low',
                'severity': 'critical',
                'value': self.health_score,
                'threshold': 50
            })
            
        # Store alerts
        for alert in alerts:
            if alert not in self.alerts:
                self.alerts.append(alert)
                logger.warning(f"⚠️ Health alert: {alert['type']} - {alert['severity']}")
                
        # Keep last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
            
    async def publish_health_update(self):
        """Publish health data update"""
        health_data = {
            'health_score': self.health_score,
            'metrics': self.metrics,
            'alerts': self.alerts[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="health_update",
            data=health_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get health monitor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'health_score': self.health_score,
            'metrics': self.metrics,
            'alerts': len(self.alerts),
            'history_size': len(self.history),
            'timestamp': datetime.now().isoformat()
        }
