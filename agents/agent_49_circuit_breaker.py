"""
AlphaEdge Agent 49 – Circuit Breaker Monitor
8-layer safety: consecutive losses, daily drawdown, weekly drawdown, correlation,
emergency, network/oracle, black swan, consensus failure
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CircuitBreakerMonitor:
    """Circuit Breaker Monitor – 8-layer safety protection system"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "circuit_breaker"
        self.running = False
        
        # Circuit breaker layers
        self.layers = {
            'consecutive_losses': {
                'status': 'closed',
                'threshold': 5,
                'current': 0,
                'description': 'Consecutive losses protection'
            },
            'daily_drawdown': {
                'status': 'closed',
                'threshold': 5,  # 5%
                'current': 0,
                'description': 'Daily drawdown protection'
            },
            'weekly_drawdown': {
                'status': 'closed',
                'threshold': 10,  # 10%
                'current': 0,
                'description': 'Weekly drawdown protection'
            },
            'correlation': {
                'status': 'closed',
                'threshold': 0.85,
                'current': 0,
                'description': 'Correlation risk protection'
            },
            'emergency': {
                'status': 'closed',
                'threshold': 1,
                'current': 0,
                'description': 'Emergency stop protection'
            },
            'network': {
                'status': 'closed',
                'threshold': 1,
                'current': 0,
                'description': 'Network/oracle failure protection'
            },
            'black_swan': {
                'status': 'closed',
                'threshold': 1,
                'current': 0,
                'description': 'Black swan event protection'
            },
            'consensus_failure': {
                'status': 'closed',
                'threshold': 1,
                'current': 0,
                'description': 'Consensus failure protection'
            }
        }
        
        self.active_layers = []
        self.breach_history = []
        self.paused = False
        
    async def start(self):
        """Start the circuit breaker monitor"""
        logger.info("Circuit Breaker Monitor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("circuit_check_request", self.handle_circuit_check)
        await self.event_bus.subscribe("trade_result", self.handle_trade_result)
        await self.event_bus.subscribe("emergency_signal", self.handle_emergency_signal)
        await self.event_bus.subscribe("network_status", self.handle_network_status)
        
        # Start monitoring cycle
        asyncio.create_task(self.run_monitoring_cycle())
        
        logger.info("Circuit Breaker Monitor running")
        
    async def stop(self):
        """Stop the circuit breaker monitor"""
        self.running = False
        logger.info("Circuit Breaker Monitor stopped")
        
    async def run_monitoring_cycle(self):
        """Run regular monitoring cycle"""
        while self.running:
            try:
                # Update all layers
                await self.update_layers()
                
                # Check for breaches
                await self.check_breaches()
                
                # Publish circuit breaker update
                await self.publish_circuit_update()
                
            except Exception as e:
                logger.error(f"Circuit monitoring cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_circuit_check(self, event: Event):
        """Handle circuit check requests"""
        if not self.running:
            return
            
        layer = event.data.get('layer')
        
        if layer:
            status = self.layers.get(layer)
        else:
            status = {
                'layers': self.layers,
                'active_layers': self.active_layers,
                'paused': self.paused
            }
            
        response = Event(
            event_type="circuit_check_response",
            data={
                'layer': layer,
                'status': status,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_trade_result(self, event: Event):
        """Handle trade results"""
        if not self.running:
            return
            
        result = event.data.get('result')
        pnl = result.get('pnl', 0)
        
        # Update consecutive losses
        if pnl < 0:
            self.layers['consecutive_losses']['current'] += 1
        else:
            self.layers['consecutive_losses']['current'] = 0
            
        # Update daily drawdown
        daily_pnl = await self.state_manager.get('daily_pnl', 0)
        daily_pnl += pnl
        await self.state_manager.set('daily_pnl', daily_pnl)
        
        if daily_pnl < 0:
            drawdown_pct = abs(daily_pnl) / await self.state_manager.get('daily_initial_capital', 10000) * 100
            self.layers['daily_drawdown']['current'] = drawdown_pct
            
        # Update weekly drawdown
        weekly_pnl = await self.state_manager.get('weekly_pnl', 0)
        weekly_pnl += pnl
        await self.state_manager.set('weekly_pnl', weekly_pnl)
        
        if weekly_pnl < 0:
            drawdown_pct = abs(weekly_pnl) / await self.state_manager.get('weekly_initial_capital', 10000) * 100
            self.layers['weekly_drawdown']['current'] = drawdown_pct
            
    async def handle_emergency_signal(self, event: Event):
        """Handle emergency signals"""
        if not self.running:
            return
            
        severity = event.data.get('severity', 'high')
        
        if severity in ['critical', 'high']:
            self.layers['emergency']['current'] = 1
            self.layers['emergency']['status'] = 'tripped'
            
            # Activate emergency circuit
            await self.activate_emergency_protocols()
            
    async def handle_network_status(self, event: Event):
        """Handle network status updates"""
        if not self.running:
            return
            
        status = event.data.get('status')
        if status == 'failed':
            self.layers['network']['current'] = 1
            self.layers['network']['status'] = 'tripped'
            
    async def update_layers(self):
        """Update all circuit breaker layers"""
        # Update correlation layer
        correlation = await self.state_manager.get('correlation_matrix', 0)
        if correlation > self.layers['correlation']['threshold']:
            self.layers['correlation']['current'] = correlation
            
        # Update black swan layer
        black_swan = await self.state_manager.get('black_swan_detected', False)
        if black_swan:
            self.layers['black_swan']['current'] = 1
            
        # Update consensus failure layer
        consensus = await self.state_manager.get('consensus_health', 100)
        if consensus < 50:
            self.layers['consensus_failure']['current'] = 1
            
    async def check_breaches(self):
        """Check for circuit breaker breaches"""
        for layer_name, layer in self.layers.items():
            if layer['status'] == 'closed':
                # Check threshold
                if layer['current'] >= layer['threshold']:
                    # Trip circuit breaker
                    layer['status'] = 'tripped'
                    self.active_layers.append(layer_name)
                    
                    # Record breach
                    self.breach_history.append({
                        'layer': layer_name,
                        'current': layer['current'],
                        'threshold': layer['threshold'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.warning(f"⚠️ Circuit breaker tripped: {layer_name} ({layer['description']})")
                    
                    # Publish breach event
                    breach_event = Event(
                        event_type="circuit_breach",
                        data={
                            'layer': layer_name,
                            'current': layer['current'],
                            'threshold': layer['threshold'],
                            'timestamp': datetime.now().isoformat()
                        },
                        source=self.agent_id
                    )
                    await self.event_bus.publish(breach_event)
                    
                    # Activate emergency protocols for critical layers
                    if layer_name in ['emergency', 'black_swan', 'consensus_failure']:
                        await self.activate_emergency_protocols()
                        
    async def activate_emergency_protocols(self):
        """Activate emergency protocols"""
        if self.paused:
            return
            
        self.paused = True
        logger.warning("⚠️ EMERGENCY PROTOCOLS ACTIVATED")
        
        # Pause trading
        await self.state_manager.set('trading_paused', True)
        
        # Publish pause event
        pause_event = Event(
            event_type="trading_pause",
            data={
                'reason': 'circuit_breaker_tripped',
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(pause_event)
        
    async def reset_layer(self, layer_name: str):
        """Reset a specific circuit breaker layer"""
        if layer_name in self.layers:
            self.layers[layer_name]['status'] = 'closed'
            self.layers[layer_name]['current'] = 0
            
            if layer_name in self.active_layers:
                self.active_layers.remove(layer_name)
                
            logger.info(f"Circuit breaker reset: {layer_name}")
            
            # Check if all layers are reset
            if not self.active_layers and self.paused:
                self.paused = False
                await self.state_manager.set('trading_paused', False)
                
                # Publish resume event
                resume_event = Event(
                    event_type="trading_resume",
                    data={
                        'reason': 'all_circuits_reset',
                        'timestamp': datetime.now().isoformat()
                    },
                    source=self.agent_id
                )
                await self.event_bus.publish(resume_event)
                
    async def publish_circuit_update(self):
        """Publish circuit breaker data update"""
        circuit_data = {
            'layers': self.layers,
            'active_layers': self.active_layers,
            'paused': self.paused,
            'breach_history': self.breach_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="circuit_update",
            data=circuit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker monitor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_layers': self.active_layers,
            'paused': self.paused,
            'breaches': len(self.breach_history),
            'layers': self.layers,
            'timestamp': datetime.now().isoformat()
        }
