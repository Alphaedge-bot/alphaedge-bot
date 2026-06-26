"""
AlphaEdge Agent 39 – Adaptive Resilience Engine
Dynamically adjusts redundancy, polling rates, resource allocation
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdaptiveResilienceEngine:
    """Adaptive Resilience Engine – Dynamic system resilience management"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "resilience"
        self.running = False
        
        # Resilience state
        self.resilience_level = 100
        self.adjustment_history = []
        self.health_metrics = {}
        
        # Configuration
        self.config = {
            'redundancy_level': 2,  # 1-3
            'polling_rate': 5,       # seconds
            'resource_allocation': 70,  # percentage
            'failure_threshold': 0.2
        }
        
    async def start(self):
        """Start the adaptive resilience engine"""
        logger.info("Adaptive Resilience Engine starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("resilience_request", self.handle_resilience_request)
        await self.event_bus.subscribe("health_report", self.handle_health_report)
        await self.event_bus.subscribe("config_update_request", self.handle_config_update)
        
        # Start resilience cycle
        asyncio.create_task(self.run_resilience_cycle())
        
        logger.info("Adaptive Resilience Engine running")
        
    async def stop(self):
        """Stop the adaptive resilience engine"""
        self.running = False
        logger.info("Adaptive Resilience Engine stopped")
        
    async def run_resilience_cycle(self):
        """Run regular resilience adaptation cycle"""
        while self.running:
            try:
                # Check system health
                await self.check_system_health()
                
                # Adjust configuration if needed
                await self.adjust_configuration()
                
                # Publish resilience update
                await self.publish_resilience_update()
                
            except Exception as e:
                logger.error(f"Resilience cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_resilience_request(self, event: Event):
        """Handle resilience requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="resilience_response",
            data={
                'resilience_level': self.resilience_level,
                'config': self.config,
                'health_metrics': self.health_metrics,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_health_report(self, event: Event):
        """Handle health reports"""
        if not self.running:
            return
            
        metrics = event.data
        self.health_metrics.update(metrics)
        
        # Check for critical health issues
        if metrics.get('health_score', 100) < 50:
            logger.warning(f"⚠️ Critical health score: {metrics['health_score']}")
            
            # Increase redundancy
            self.config['redundancy_level'] = min(3, self.config['redundancy_level'] + 1)
            
    async def handle_config_update(self, event: Event):
        """Handle configuration update requests"""
        if not self.running:
            return
            
        new_config = event.data.get('config', {})
        
        # Validate and apply updates
        for key, value in new_config.items():
            if key in self.config:
                self.config[key] = value
                
        logger.info(f"Configuration updated: {new_config}")
        
        response = Event(
            event_type="config_update_response",
            data={
                'updated': True,
                'config': self.config,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def check_system_health(self):
        """Check overall system health"""
        # Get metrics from state
        health_score = await self.state_manager.get('health_score', 100)
        active_agents = await self.state_manager.get('active_agents', 0)
        total_agents = await self.state_manager.get('total_agents', 72)
        
        # Calculate resilience level
        # Higher health score = higher resilience
        base_resilience = health_score / 100 * 100
        
        # Adjust for active agents ratio
        agent_ratio = active_agents / total_agents if total_agents > 0 else 0
        agent_factor = agent_ratio * 20  # Up to 20 points
        
        # Adjust for recent failures
        failure_rate = await self.state_manager.get('failure_rate', 0)
        failure_penalty = failure_rate * 50  # Up to 50 points penalty
        
        self.resilience_level = max(0, min(100, base_resilience + agent_factor - failure_penalty))
        
        # Store resilience level
        await self.state_manager.set('resilience_level', self.resilience_level)
        
    async def adjust_configuration(self):
        """Adjust configuration based on resilience level"""
        previous_config = self.config.copy()
        
        if self.resilience_level < 40:
            # Critical: Increase redundancy
            self.config['redundancy_level'] = 3
            self.config['polling_rate'] = 2
            self.config['resource_allocation'] = 50
            
            # Activate emergency protocols
            await self.activate_emergency_protocols()
            
        elif self.resilience_level < 60:
            # High risk: Increase monitoring
            self.config['redundancy_level'] = max(2, self.config['redundancy_level'])
            self.config['polling_rate'] = 3
            self.config['resource_allocation'] = 60
            
        elif self.resilience_level < 80:
            # Moderate: Normal operations
            self.config['redundancy_level'] = 2
            self.config['polling_rate'] = 5
            self.config['resource_allocation'] = 70
            
        else:
            # Optimal: Efficient operations
            self.config['redundancy_level'] = 1
            self.config['polling_rate'] = 10
            self.config['resource_allocation'] = 80
            
        # Log adjustment
        if previous_config != self.config:
            self.adjustment_history.append({
                'previous': previous_config,
                'new': self.config,
                'reason': f'Resilience level: {self.resilience_level}',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Configuration adjusted: {self.config}")
            
        # Store updated config
        await self.state_manager.set('resilience_config', self.config)
        
    async def activate_emergency_protocols(self):
        """Activate emergency protocols for critical situations"""
        logger.warning("⚠️ EMERGENCY PROTOCOLS ACTIVATED")
        
        # Publish emergency event
        emergency_event = Event(
            event_type="emergency_protocols_active",
            data={
                'reason': 'Resilience level below 40%',
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(emergency_event)
        
        # Increase redundancy
        self.config['redundancy_level'] = 3
        
        # Reduce polling rate for conservation
        self.config['polling_rate'] = 1
        
        # Reduce resource usage
        self.config['resource_allocation'] = 30
        
    async def publish_resilience_update(self):
        """Publish resilience data update"""
        resilience_data = {
            'resilience_level': self.resilience_level,
            'config': self.config,
            'health_metrics': self.health_metrics,
            'adjustment_history': self.adjustment_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="resilience_update",
            data=resilience_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get resilience engine status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'resilience_level': self.resilience_level,
            'config': self.config,
            'adjustment_count': len(self.adjustment_history),
            'timestamp': datetime.now().isoformat()
        }
