"""
AlphaEdge Agent 52 – Critic Agent
Adversarial validation (synthetic slippage, lag, spoofing, flash crash)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CriticAgent:
    """Critic Agent – Adversarial validation and testing"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "critic"
        self.running = False
        
        # Critic state
        self.test_results = []
        self.attack_simulations = []
        self.vulnerabilities = []
        
        # Attack types
        self.attacks = [
            'slippage',
            'lag',
            'spoofing',
            'flash_crash',
            'front_running',
            'data_manipulation'
        ]
        
        # Test configuration
        self.config = {
            'test_interval': 300,  # 5 minutes
            'max_test_duration': 60,  # 1 minute
            'severity_level': 'medium'
        }
        
    async def start(self):
        """Start the critic agent"""
        logger.info("Critic Agent starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("critic_test_request", self.handle_test_request)
        await self.event_bus.subscribe("attack_simulation", self.handle_attack_simulation)
        await self.event_bus.subscribe("vulnerability_report", self.handle_vulnerability_report)
        
        # Start critic cycle
        asyncio.create_task(self.run_critic_cycle())
        
        logger.info("Critic Agent running")
        
    async def stop(self):
        """Stop the critic agent"""
        self.running = False
        logger.info("Critic Agent stopped")
        
    async def run_critic_cycle(self):
        """Run regular critic cycle"""
        while self.running:
            try:
                # Run adversarial tests
                await self.run_adversarial_tests()
                
                # Analyze vulnerabilities
                await self.analyze_vulnerabilities()
                
                # Publish critic update
                await self.publish_critic_update()
                
            except Exception as e:
                logger.error(f"Critic cycle error: {e}")
                
            await asyncio.sleep(self.config['test_interval'])
            
    async def handle_test_request(self, event: Event):
        """Handle test requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        test_type = event.data.get('test_type')
        
        logger.info(f"Test request: {request_id} ({test_type})")
        
        # Run specific test
        result = await self.run_test(test_type)
        
        response = Event(
            event_type="critic_test_response",
            data={
                'request_id': request_id,
                'test_type': test_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_attack_simulation(self, event: Event):
        """Handle attack simulation events"""
        if not self.running:
            return
            
        attack_type = event.data.get('attack_type')
        severity = event.data.get('severity', 'medium')
        
        # Simulate attack
        result = await self.simulate_attack(attack_type, severity)
        
        self.attack_simulations.append({
            'attack_type': attack_type,
            'severity': severity,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    async def handle_vulnerability_report(self, event: Event):
        """Handle vulnerability reports"""
        if not self.running:
            return
            
        vulnerability = event.data.get('vulnerability')
        severity = event.data.get('severity', 'low')
        
        self.vulnerabilities.append({
            'vulnerability': vulnerability,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.warning(f"⚠️ Vulnerability detected: {vulnerability} ({severity})")
        
    async def run_adversarial_tests(self):
        """Run adversarial tests"""
        # Select random attack
        attack_type = random.choice(self.attacks)
        severity = random.choice(['low', 'medium', 'high'])
        
        # Run test
        result = await self.simulate_attack(attack_type, severity)
        
        # Store result
        self.test_results.append({
            'attack_type': attack_type,
            'severity': severity,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 100 tests
        if len(self.test_results) > 100:
            self.test_results = self.test_results[-100:]
            
        logger.info(f"Adversarial test: {attack_type} ({severity}) - {result['status']}")
        
    async def simulate_attack(self, attack_type: str, severity: str) -> Dict:
        """Simulate an attack"""
        start_time = datetime.now()
        
        if attack_type == 'slippage':
            result = await self.simulate_slippage(severity)
        elif attack_type == 'lag':
            result = await self.simulate_lag(severity)
        elif attack_type == 'spoofing':
            result = await self.simulate_spoofing(severity)
        elif attack_type == 'flash_crash':
            result = await self.simulate_flash_crash(severity)
        elif attack_type == 'front_running':
            result = await self.simulate_front_running(severity)
        elif attack_type == 'data_manipulation':
            result = await self.simulate_data_manipulation(severity)
        else:
            result = {'status': 'unknown_attack'}
            
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        result['duration'] = duration
        
        return result
        
    async def simulate_slippage(self, severity: str) -> Dict:
        """Simulate slippage attack"""
        slippage_amount = {
            'low': random.uniform(0.01, 0.02),
            'medium': random.uniform(0.02, 0.05),
            'high': random.uniform(0.05, 0.10)
        }.get(severity, 0.02)
        
        # Simulate slippage
        await asyncio.sleep(0.1)
        
        return {
            'status': 'detected' if random.random() > 0.3 else 'missed',
            'slippage': slippage_amount,
            'detection_confidence': random.uniform(0.6, 0.9)
        }
        
    async def simulate_lag(self, severity: str) -> Dict:
        """Simulate network lag"""
        lag_ms = {
            'low': random.uniform(100, 500),
            'medium': random.uniform(500, 1000),
            'high': random.uniform(1000, 2000)
        }.get(severity, 500)
        
        # Simulate lag
        await asyncio.sleep(lag_ms / 1000)
        
        return {
            'status': 'detected' if random.random() > 0.4 else 'missed',
            'lag_ms': lag_ms,
            'detection_confidence': random.uniform(0.5, 0.85)
        }
        
    async def simulate_spoofing(self, severity: str) -> Dict:
        """Simulate order book spoofing"""
        spoof_depth = {
            'low': random.randint(10, 50),
            'medium': random.randint(50, 100),
            'high': random.randint(100, 200)
        }.get(severity, 50)
        
        # Simulate spoofing
        await asyncio.sleep(0.2)
        
        return {
            'status': 'detected' if random.random() > 0.35 else 'missed',
            'spoof_depth': spoof_depth,
            'detection_confidence': random.uniform(0.4, 0.8)
        }
        
    async def simulate_flash_crash(self, severity: str) -> Dict:
        """Simulate flash crash"""
        crash_pct = {
            'low': random.uniform(5, 10),
            'medium': random.uniform(10, 20),
            'high': random.uniform(20, 30)
        }.get(severity, 10)
        
        # Simulate flash crash
        await asyncio.sleep(0.3)
        
        return {
            'status': 'detected' if random.random() > 0.25 else 'missed',
            'crash_pct': crash_pct,
            'detection_confidence': random.uniform(0.7, 0.95)
        }
        
    async def simulate_front_running(self, severity: str) -> Dict:
        """Simulate front-running"""
        front_run_amount = {
            'low': random.uniform(0.01, 0.02),
            'medium': random.uniform(0.02, 0.04),
            'high': random.uniform(0.04, 0.08)
        }.get(severity, 0.02)
        
        # Simulate front-running
        await asyncio.sleep(0.15)
        
        return {
            'status': 'detected' if random.random() > 0.3 else 'missed',
            'front_run_amount': front_run_amount,
            'detection_confidence': random.uniform(0.5, 0.85)
        }
        
    async def simulate_data_manipulation(self, severity: str) -> Dict:
        """Simulate data manipulation"""
        manipulation_pct = {
            'low': random.uniform(1, 3),
            'medium': random.uniform(3, 7),
            'high': random.uniform(7, 15)
        }.get(severity, 3)
        
        # Simulate data manipulation
        await asyncio.sleep(0.2)
        
        return {
            'status': 'detected' if random.random() > 0.4 else 'missed',
            'manipulation_pct': manipulation_pct,
            'detection_confidence': random.uniform(0.4, 0.8)
        }
        
    async def analyze_vulnerabilities(self):
        """Analyze vulnerabilities from test results"""
        recent_tests = self.test_results[-20:]
        
        # Count missed detections by attack type
        missed_by_type = {}
        
        for test in recent_tests:
            attack_type = test.get('attack_type')
            if test.get('result', {}).get('status') == 'missed':
                missed_by_type[attack_type] = missed_by_type.get(attack_type, 0) + 1
                
        # Generate vulnerabilities
        for attack_type, count in missed_by_type.items():
            if count > 3:  # More than 3 misses in 20 tests
                vulnerability = f"Vulnerability to {attack_type} attacks"
                if vulnerability not in [v['vulnerability'] for v in self.vulnerabilities]:
                    self.vulnerabilities.append({
                        'vulnerability': vulnerability,
                        'severity': 'high' if count > 5 else 'medium',
                        'detected_at': datetime.now().isoformat()
                    })
                    
    async def run_test(self, test_type: str) -> Dict:
        """Run a specific test"""
        if test_type in self.attacks:
            return await self.simulate_attack(test_type, self.config['severity_level'])
        else:
            return {'status': 'unknown_test'}
            
    async def publish_critic_update(self):
        """Publish critic data update"""
        critic_data = {
            'test_results': self.test_results[-5:],
            'vulnerabilities': self.vulnerabilities,
            'attack_simulations': len(self.attack_simulations),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="critic_update",
            data=critic_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get critic agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'test_results': len(self.test_results),
            'vulnerabilities': len(self.vulnerabilities),
            'attack_simulations': len(self.attack_simulations),
            'timestamp': datetime.now().isoformat()
        }
