"""
AlphaEdge Agent 35 – Execution Quality Dashboard
Monitor execution quality, slippage, latency, and performance metrics
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ExecutionQualityDashboard:
    """Execution Quality Dashboard – Monitor execution performance"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "execution_dashboard"
        self.running = False
        
        # Dashboard state
        self.metrics = {
            'total_executions': 0,
            'avg_slippage': 0,
            'avg_latency': 0,
            'success_rate': 100,
            'best_dex': None,
            'worst_dex': None
        }
        self.execution_history = []
        self.dex_performance = {}
        self.alerts = []
        
    async def start(self):
        """Start the execution quality dashboard"""
        logger.info("Execution Quality Dashboard starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("execution_result", self.handle_execution_result)
        await self.event_bus.subscribe("dashboard_request", self.handle_dashboard_request)
        await self.event_bus.subscribe("alert_config_request", self.handle_alert_config)
        
        # Start dashboard cycle
        asyncio.create_task(self.run_dashboard_cycle())
        
        logger.info("Execution Quality Dashboard running")
        
    async def stop(self):
        """Stop the execution quality dashboard"""
        self.running = False
        logger.info("Execution Quality Dashboard stopped")
        
    async def run_dashboard_cycle(self):
        """Run regular dashboard update cycle"""
        while self.running:
            try:
                # Update metrics
                await self.update_metrics()
                
                # Check alerts
                await self.check_alerts()
                
                # Publish dashboard update
                await self.publish_dashboard_update()
                
            except Exception as e:
                logger.error(f"Dashboard cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_execution_result(self, event: Event):
        """Handle execution results"""
        if not self.running:
            return
            
        execution = event.data
        self.execution_history.append(execution)
        
        # Keep last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history.pop(0)
            
        # Update dex performance
        dex = execution.get('dex', 'unknown')
        if dex not in self.dex_performance:
            self.dex_performance[dex] = {
                'executions': 0,
                'slippage_sum': 0,
                'latency_sum': 0,
                'successes': 0
            }
            
        self.dex_performance[dex]['executions'] += 1
        self.dex_performance[dex]['slippage_sum'] += execution.get('slippage', 0)
        self.dex_performance[dex]['latency_sum'] += execution.get('latency', 0)
        if execution.get('status') == 'success':
            self.dex_performance[dex]['successes'] += 1
            
        logger.info(f"Execution recorded: {execution.get('dex')} - {execution.get('slippage')}")
        
    async def update_metrics(self):
        """Update dashboard metrics"""
        if not self.execution_history:
            return
            
        # Calculate metrics
        total = len(self.execution_history)
        total_slippage = sum(e.get('slippage', 0) for e in self.execution_history)
        total_latency = sum(e.get('latency', 0) for e in self.execution_history)
        successes = len([e for e in self.execution_history if e.get('status') == 'success'])
        
        self.metrics = {
            'total_executions': total,
            'avg_slippage': total_slippage / total if total > 0 else 0,
            'avg_latency': total_latency / total if total > 0 else 0,
            'success_rate': (successes / total * 100) if total > 0 else 0
        }
        
        # Update best/worst DEX
        if self.dex_performance:
            avg_slippage_by_dex = {
                dex: data['slippage_sum'] / data['executions']
                for dex, data in self.dex_performance.items()
                if data['executions'] > 0
            }
            if avg_slippage_by_dex:
                self.metrics['best_dex'] = min(avg_slippage_by_dex, key=avg_slippage_by_dex.get)
                self.metrics['worst_dex'] = max(avg_slippage_by_dex, key=avg_slippage_by_dex.get)
                
        # Store metrics
        await self.state_manager.set('execution_metrics', self.metrics)
        
    async def check_alerts(self):
        """Check for alerts"""
        # Slippage alert
        if self.metrics['avg_slippage'] > 0.01:
            self.alerts.append({
                'type': 'slippage',
                'severity': 'high',
                'message': f"Avg slippage {self.metrics['avg_slippage']:.2f}% exceeds 1%",
                'timestamp': datetime.now().isoformat()
            })
            
        # Success rate alert
        if self.metrics['success_rate'] < 90:
            self.alerts.append({
                'type': 'success_rate',
                'severity': 'critical',
                'message': f"Success rate {self.metrics['success_rate']:.1f}% below 90%",
                'timestamp': datetime.now().isoformat()
            })
            
        # Latency alert
        if self.metrics['avg_latency'] > 500:
            self.alerts.append({
                'type': 'latency',
                'severity': 'medium',
                'message': f"Avg latency {self.metrics['avg_latency']:.1f}ms exceeds 500ms",
                'timestamp': datetime.now().isoformat()
            })
            
        # Keep last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
            
    async def handle_dashboard_request(self, event: Event):
        """Handle dashboard requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="dashboard_response",
            data={
                'metrics': self.metrics,
                'dex_performance': self.dex_performance,
                'alerts': self.alerts[-5:],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_alert_config(self, event: Event):
        """Handle alert configuration requests"""
        if not self.running:
            return
            
        # In production, handle alert configuration
        # For now, just log
        logger.info("Alert config request received")
        
        response = Event(
            event_type="alert_config_response",
            data={
                'status': 'configured',
                'alerts': self.alerts,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_dashboard_update(self):
        """Publish dashboard data update"""
        dashboard_data = {
            'metrics': self.metrics,
            'dex_performance': self.dex_performance,
            'recent_executions': self.execution_history[-10:],
            'alerts': self.alerts[-5:],
            'total_executions': len(self.execution_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="dashboard_update",
            data=dashboard_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get execution dashboard status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_executions': len(self.execution_history),
            'active_alerts': len(self.alerts),
            'metrics': self.metrics,
            'dex_count': len(self.dex_performance),
            'timestamp': datetime.now().isoformat()
        }
