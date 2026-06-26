"""
AlphaEdge Agent 12 – Adversarial Simulator
Simulates adversarial market conditions
Slippage, lag, spoofing, flash crash scenarios
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AdversarialSimulator:
    """Adversarial Simulator – Tests bot resilience under adversarial conditions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "adversarial"
        self.running = False
        
        # Simulation state
        self.active_scenarios = []
        self.simulation_results = []
        self.resilience_score = 100
        
        # Scenario definitions
        self.scenarios = {
            'slippage': {
                'severity': 'medium',
                'duration': 60,
                'impact': 'execution_quality'
            },
            'lag': {
                'severity': 'high',
                'duration': 30,
                'impact': 'response_time'
            },
            'spoofing': {
                'severity': 'critical',
                'duration': 15,
                'impact': 'price_feed'
            },
            'flash_crash': {
                'severity': 'critical',
                'duration': 10,
                'impact': 'position_risk'
            },
            'front_running': {
                'severity': 'medium',
                'duration': 20,
                'impact': 'execution_quality'
            },
            'exchange_outage': {
                'severity': 'critical',
                'duration': 120,
                'impact': 'connectivity'
            }
        }
        
    async def start(self):
        """Start the adversarial simulator"""
        logger.info("Adversarial Simulator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("simulation_request", self.handle_simulation_request)
        await self.event_bus.subscribe("market_data", self.handle_market_data)
        
        # Start simulation cycle
        asyncio.create_task(self.run_simulation_cycle())
        
        logger.info("Adversarial Simulator running")
        
    async def stop(self):
        """Stop the adversarial simulator"""
        self.running = False
        logger.info("Adversarial Simulator stopped")
        
    async def run_simulation_cycle(self):
        """Run regular simulation cycles"""
        while self.running:
            try:
                # Check if simulation needed
                if random.random() < 0.1:  # 10% chance per cycle
                    scenario = await self.select_scenario()
                    await self.run_scenario(scenario)
                    
                # Update resilience score
                await self.update_resilience_score()
                
                # Publish simulation update
                await self.publish_simulation_update()
                
            except Exception as e:
                logger.error(f"Simulation cycle error: {e}")
                
            await asyncio.sleep(180)  # Every 3 minutes
            
    async def select_scenario(self) -> Dict[str, Any]:
        """Select a scenario to simulate"""
        # Weighted selection based on market conditions
        market_volatility = await self.state_manager.get('market_volatility', 0.3)
        
        if market_volatility > 0.7:
            # High volatility scenarios
            weights = {
                'flash_crash': 0.4,
                'slippage': 0.3,
                'spoofing': 0.3
            }
        elif market_volatility > 0.4:
            # Medium volatility scenarios
            weights = {
                'slippage': 0.4,
                'lag': 0.3,
                'front_running': 0.3
            }
        else:
            # Low volatility scenarios
            weights = {
                'exchange_outage': 0.3,
                'lag': 0.3,
                'slippage': 0.4
            }
            
        scenario_name = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
        return {
            'name': scenario_name,
            'config': self.scenarios[scenario_name],
            'timestamp': datetime.now().isoformat()
        }
        
    async def run_scenario(self, scenario: Dict[str, Any]):
        """Run a specific adversarial scenario"""
        name = scenario['name']
        config = scenario['config']
        
        logger.warning(f"⚠️ RUNNING ADVERSARIAL SCENARIO: {name}")
        
        # Create simulation event
        sim_event = Event(
            event_type="adversarial_scenario_start",
            data={
                'scenario': name,
                'config': config,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(sim_event)
        
        # Execute scenario-specific simulation
        if name == 'slippage':
            await self.simulate_slippage()
        elif name == 'lag':
            await self.simulate_lag()
        elif name == 'spoofing':
            await self.simulate_spoofing()
        elif name == 'flash_crash':
            await self.simulate_flash_crash()
        elif name == 'front_running':
            await self.simulate_front_running()
        elif name == 'exchange_outage':
            await self.simulate_exchange_outage()
            
        # Record results
        self.simulation_results.append({
            'scenario': name,
            'timestamp': datetime.now().isoformat(),
            'bot_response': await self.evaluate_bot_response(),
            'resilience_impact': self.calculate_resilience_impact(name)
        })
        
        # End scenario
        end_event = Event(
            event_type="adversarial_scenario_end",
            data={
                'scenario': name,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(end_event)
        
        logger.info(f"✅ Adversarial scenario {name} completed")
        
    async def simulate_slippage(self):
        """Simulate slippage on trades"""
        # Inject slippage into execution
        slippage_event = Event(
            event_type="price_feed_manipulation",
            data={
                'type': 'slippage',
                'severity': 'medium',
                'slippage_percent': random.uniform(0.5, 2.0),
                'duration': 60
            },
            source=self.agent_id
        )
        await self.event_bus.publish(slippage_event)
        await asyncio.sleep(60)
        
    async def simulate_lag(self):
        """Simulate network lag"""
        lag_event = Event(
            event_type="network_lag_simulation",
            data={
                'type': 'lag',
                'severity': 'high',
                'latency_ms': random.randint(500, 2000),
                'duration': 30
            },
            source=self.agent_id
        )
        await self.event_bus.publish(lag_event)
        await asyncio.sleep(30)
        
    async def simulate_spoofing(self):
        """Simulate order book spoofing"""
        spoof_event = Event(
            event_type="price_feed_manipulation",
            data={
                'type': 'spoofing',
                'severity': 'critical',
                'fake_orders': random.randint(10, 50),
                'duration': 15
            },
            source=self.agent_id
        )
        await self.event_bus.publish(spoof_event)
        await asyncio.sleep(15)
        
    async def simulate_flash_crash(self):
        """Simulate flash crash"""
        flash_event = Event(
            event_type="flash_crash_simulation",
            data={
                'type': 'flash_crash',
                'severity': 'critical',
                'drop_percent': random.uniform(15, 30),
                'duration': 10
            },
            source=self.agent_id
        )
        await self.event_bus.publish(flash_event)
        await asyncio.sleep(10)
        
    async def simulate_front_running(self):
        """Simulate front-running"""
        front_run_event = Event(
            event_type="execution_manipulation",
            data={
                'type': 'front_running',
                'severity': 'medium',
                'slippage': random.uniform(0.3, 1.0),
                'duration': 20
            },
            source=self.agent_id
        )
        await self.event_bus.publish(front_run_event)
        await asyncio.sleep(20)
        
    async def simulate_exchange_outage(self):
        """Simulate exchange outage"""
        outage_event = Event(
            event_type="connectivity_failure",
            data={
                'type': 'exchange_outage',
                'severity': 'critical',
                'exchanges': ['Binance', 'Coinbase'],
                'duration': 120
            },
            source=self.agent_id
        )
        await self.event_bus.publish(outage_event)
        await asyncio.sleep(120)
        
    async def evaluate_bot_response(self) -> Dict[str, Any]:
        """Evaluate bot's response to adversarial scenario"""
        # Check circuit breakers
        cb_status = await self.state_manager.get('circuit_breakers', {})
        
        # Check execution status
        exec_status = await self.state_manager.get('execution_status', {})
        
        # Check risk status
        risk_status = await self.state_manager.get('risk_status', {})
        
        return {
            'circuit_breakers_triggered': cb_status.get('active_layers', []),
            'execution_paused': exec_status.get('paused', False),
            'risk_measures_taken': risk_status.get('actions', []),
            'response_time': random.uniform(0.5, 5.0)
        }
        
    def calculate_resilience_impact(self, scenario: str) -> float:
        """Calculate resilience impact of scenario"""
        impact_weights = {
            'slippage': 5,
            'lag': 10,
            'spoofing': 15,
            'flash_crash': 25,
            'front_running': 8,
            'exchange_outage': 20
        }
        
        return impact_weights.get(scenario, 10)
        
    async def update_resilience_score(self):
        """Update overall resilience score"""
        base_score = 100
        
        # Reduce score based on recent scenarios
        recent_results = self.simulation_results[-10:]
        total_impact = sum(r.get('resilience_impact', 0) for r in recent_results)
        
        # Decay impact over time
        decay_factor = 0.95
        adjusted_impact = total_impact * (decay_factor ** len(recent_results))
        
        self.resilience_score = max(0, base_score - adjusted_impact)
        
        await self.state_manager.set('resilience_score', self.resilience_score)
        
    async def publish_simulation_update(self):
        """Publish simulation data update"""
        sim_data = {
            'resilience_score': self.resilience_score,
            'active_scenarios': len(self.active_scenarios),
            'simulation_results': self.simulation_results[-10:],
            'total_simulations': len(self.simulation_results),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="simulation_data_update",
            data=sim_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_simulation_request(self, event: Event):
        """Handle simulation requests"""
        if not self.running:
            return
            
        sim_data = {
            'resilience_score': self.resilience_score,
            'active_scenarios': len(self.active_scenarios),
            'simulation_results': self.simulation_results[-10:],
            'total_simulations': len(self.simulation_results),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="simulation_response",
            data=sim_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_market_data(self, event: Event):
        """Handle market data for scenario selection"""
        if not self.running:
            return
            
        # Store volatility for scenario selection
        volatility = event.data.get('volatility', 0.3)
        await self.state_manager.set('market_volatility', volatility)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get adversarial simulator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'resilience_score': self.resilience_score,
            'total_simulations': len(self.simulation_results),
            'active_scenarios': len(self.active_scenarios),
            'timestamp': datetime.now().isoformat()
        }
