"""
AlphaEdge Agent 36 – Predictive Failure Simulator
Monte-Carlo + agent-based simulation of 10k+ failure scenarios
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import math

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class PredictiveFailureSimulator:
    """Predictive Failure Simulator – Monte-Carlo and agent-based failure simulation"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "failure_simulator"
        self.running = False
        
        # Simulation state
        self.simulation_results = []
        self.failure_probabilities = {}
        self.recovery_times = {}
        self.risk_heatmap = {}
        
        # Simulation parameters
        self.scenarios = [
            'network_outage',
            'rpc_failure',
            'exchange_outage',
            'correlation_break',
            'flash_crash',
            'liquidity_crisis',
            'wallet_compromise',
            'oracle_failure'
        ]
        
        self.simulation_count = 0
        self.max_simulations = 10000
        
    async def start(self):
        """Start the failure simulator"""
        logger.info("Predictive Failure Simulator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("simulation_request", self.handle_simulation_request)
        await self.event_bus.subscribe("risk_analysis_request", self.handle_risk_analysis)
        await self.event_bus.subscribe("recovery_plan_request", self.handle_recovery_plan)
        
        # Start simulation cycle
        asyncio.create_task(self.run_simulation_cycle())
        
        logger.info("Predictive Failure Simulator running")
        
    async def stop(self):
        """Stop the failure simulator"""
        self.running = False
        logger.info("Predictive Failure Simulator stopped")
        
    async def run_simulation_cycle(self):
        """Run regular simulation cycle"""
        while self.running:
            try:
                # Run simulations if needed
                if self.simulation_count < self.max_simulations:
                    await self.run_scenario_simulations()
                    
                # Update risk metrics
                await self.update_risk_metrics()
                
                # Publish simulation update
                await self.publish_simulation_update()
                
            except Exception as e:
                logger.error(f"Simulation cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_simulation_request(self, event: Event):
        """Handle simulation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        scenario = event.data.get('scenario')
        iterations = event.data.get('iterations', 100)
        
        logger.info(f"Simulation request: {request_id} ({scenario})")
        
        # Run simulation
        results = await self.run_simulation(scenario, iterations)
        
        # Send response
        response = Event(
            event_type="simulation_result",
            data={
                'request_id': request_id,
                'scenario': scenario,
                'results': results,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def run_simulation(self, scenario: str, iterations: int) -> Dict:
        """Run simulation for a specific scenario"""
        results = {
            'scenario': scenario,
            'iterations': iterations,
            'success_rate': 0,
            'failure_rate': 0,
            'avg_recovery_time': 0,
            'failure_modes': {}
        }
        
        failures = 0
        recovery_times = []
        failure_counts = {}
        
        for _ in range(iterations):
            # Simulate failure occurrence
            failure, recovery_time, failure_mode = await self.simulate_failure(scenario)
            
            if failure:
                failures += 1
                recovery_times.append(recovery_time)
                failure_counts[failure_mode] = failure_counts.get(failure_mode, 0) + 1
                
        # Calculate metrics
        total = iterations
        success = total - failures
        
        results['success_rate'] = success / total * 100
        results['failure_rate'] = failures / total * 100
        results['avg_recovery_time'] = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        results['failure_modes'] = failure_counts
        
        self.simulation_count += 1
        self.simulation_results.append(results)
        
        return results
        
    async def simulate_failure(self, scenario: str) -> tuple:
        """Simulate a single failure scenario"""
        # Base failure probability
        base_probabilities = {
            'network_outage': 0.05,
            'rpc_failure': 0.08,
            'exchange_outage': 0.03,
            'correlation_break': 0.02,
            'flash_crash': 0.01,
            'liquidity_crisis': 0.04,
            'wallet_compromise': 0.005,
            'oracle_failure': 0.06
        }
        
        probability = base_probabilities.get(scenario, 0.05)
        
        # Adjust based on current conditions
        health_score = await self.state_manager.get('health_score', 100)
        if health_score < 80:
            probability *= 1.5
            
        # Determine if failure occurs
        random_value = random.random()
        failure = random_value < probability
        
        if failure:
            # Determine failure mode
            failure_modes = [
                'partial', 'full', 'degraded', 'delayed'
            ]
            mode = random.choice(failure_modes)
            
            # Recovery time (seconds)
            recovery_time = random.expovariate(0.01)  # Mean 100 seconds
            recovery_time = min(600, max(1, recovery_time))  # Cap at 10 minutes
            
            return True, recovery_time, mode
        else:
            return False, 0, 'none'
            
    async def update_risk_metrics(self):
        """Update risk metrics based on simulations"""
        if not self.simulation_results:
            return
            
        # Calculate failure probabilities by scenario
        for scenario in self.scenarios:
            results = [r for r in self.simulation_results if r['scenario'] == scenario]
            if results:
                avg_failure_rate = sum(r['failure_rate'] for r in results) / len(results)
                self.failure_probabilities[scenario] = avg_failure_rate / 100
                
        # Calculate recovery times
        for scenario in self.scenarios:
            results = [r for r in self.simulation_results if r['scenario'] == scenario]
            if results:
                avg_recovery = sum(r['avg_recovery_time'] for r in results) / len(results)
                self.recovery_times[scenario] = avg_recovery
                
        # Create risk heatmap
        self.risk_heatmap = {
            scenario: {
                'probability': self.failure_probabilities.get(scenario, 0),
                'recovery_time': self.recovery_times.get(scenario, 0),
                'risk_score': self.calculate_risk_score(
                    self.failure_probabilities.get(scenario, 0),
                    self.recovery_times.get(scenario, 0)
                )
            }
            for scenario in self.scenarios
        }
        
        # Store in state
        await self.state_manager.set('risk_heatmap', self.risk_heatmap)
        
    def calculate_risk_score(self, probability: float, recovery_time: float) -> float:
        """Calculate risk score (0-100)"""
        # Higher probability and recovery time = higher risk
        prob_score = min(100, probability * 2000)  # 0.05 = 100
        time_score = min(100, recovery_time / 6)  # 600s = 100
        
        return (prob_score * 0.6) + (time_score * 0.4)
        
    async def run_scenario_simulations(self):
        """Run simulations for all scenarios"""
        for scenario in self.scenarios:
            await self.run_simulation(scenario, 100)  # Run 100 iterations per scenario
            
        logger.info(f"Completed {self.simulation_count} simulations")
        
    async def handle_risk_analysis(self, event: Event):
        """Handle risk analysis requests"""
        if not self.running:
            return
            
        response = Event(
            event_type="risk_analysis_response",
            data={
                'risk_heatmap': self.risk_heatmap,
                'failure_probabilities': self.failure_probabilities,
                'recovery_times': self.recovery_times,
                'total_simulations': self.simulation_count,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_recovery_plan(self, event: Event):
        """Handle recovery plan requests"""
        if not self.running:
            return
            
        scenario = event.data.get('scenario')
        if scenario:
            plan = self.generate_recovery_plan(scenario)
        else:
            plan = self.generate_all_recovery_plans()
            
        response = Event(
            event_type="recovery_plan_response",
            data={
                'scenario': scenario,
                'plan': plan,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    def generate_recovery_plan(self, scenario: str) -> Dict:
        """Generate recovery plan for a scenario"""
        plans = {
            'network_outage': {
                'steps': [
                    'Switch to backup network',
                    'Enable 5G failover',
                    'Increase polling intervals'
                ],
                'estimated_time': 30
            },
            'rpc_failure': {
                'steps': [
                    'Switch to backup RPC',
                    'Enable fallback provider',
                    'Reduce request frequency'
                ],
                'estimated_time': 15
            },
            'exchange_outage': {
                'steps': [
                    'Switch to backup DEX',
                    'Enable circuit breaker',
                    'Pause trading'
                ],
                'estimated_time': 60
            },
            'flash_crash': {
                'steps': [
                    'Emergency stop',
                    'Exit positions',
                    'Convert to stablecoins',
                    'Wait for recovery'
                ],
                'estimated_time': 120
            },
            'oracle_failure': {
                'steps': [
                    'Switch to backup oracle',
                    'Enable fallback price feed',
                    'Increase deviation tolerance'
                ],
                'estimated_time': 20
            }
        }
        
        return plans.get(scenario, {
            'steps': ['Activate general fallback procedures'],
            'estimated_time': 60
        })
        
    def generate_all_recovery_plans(self) -> Dict:
        """Generate recovery plans for all scenarios"""
        return {
            scenario: self.generate_recovery_plan(scenario)
            for scenario in self.scenarios
        }
        
    async def publish_simulation_update(self):
        """Publish simulation data update"""
        simulation_data = {
            'total_simulations': self.simulation_count,
            'risk_heatmap': self.risk_heatmap,
            'failure_probabilities': self.failure_probabilities,
            'recovery_times': self.recovery_times,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="simulation_update",
            data=simulation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get failure simulator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_simulations': self.simulation_count,
            'max_simulations': self.max_simulations,
            'scenarios': len(self.scenarios),
            'risk_heatmap': self.risk_heatmap,
            'timestamp': datetime.now().isoformat()
        }
