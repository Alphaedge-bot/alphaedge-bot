"""
AlphaEdge Agent 64 – Profit Taking Auditor
Audit exit quality, profit capture rate (>80%), slippage (<0.5%), reward/punish
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingAuditor:
    """Profit Taking Auditor – Audits profit-taking execution quality"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "profit_taking_auditor"
        self.running = False
        
        # Audit state
        self.audit_results = []
        self.quality_scores = {}
        self.reward_history = []
        self.penalty_history = []
        
        # Configuration
        self.config = {
            'profit_capture_target': 0.80,  # 80%
            'slippage_target': 0.005,  # 0.5%
            'min_trades_for_audit': 5,
            'reward_factor': 0.1,  # 10% reward boost
            'penalty_factor': 0.05  # 5% penalty
        }
        
    async def start(self):
        """Start the profit taking auditor"""
        logger.info("Profit Taking Auditor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("audit_profit_take", self.handle_audit_profit_take)
        await self.event_bus.subscribe("quality_request", self.handle_quality_request)
        await self.event_bus.subscribe("reward_penalty_request", self.handle_reward_penalty_request)
        
        # Start audit cycle
        asyncio.create_task(self.run_audit_cycle())
        
        logger.info("Profit Taking Auditor running")
        
    async def stop(self):
        """Stop the profit taking auditor"""
        self.running = False
        logger.info("Profit Taking Auditor stopped")
        
    async def run_audit_cycle(self):
        """Run regular audit cycle"""
        while self.running:
            try:
                # Review pending audits
                await self.review_audits()
                
                # Update quality scores
                await self.update_quality_scores()
                
                # Apply rewards/penalties
                await self.apply_rewards_penalties()
                
                # Publish audit update
                await self.publish_audit_update()
                
            except Exception as e:
                logger.error(f"Audit cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_audit_profit_take(self, event: Event):
        """Handle profit taking audit requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        execution = event.data.get('execution')
        
        # Perform audit
        result = await self.audit_execution(execution)
        
        response = Event(
            event_type="audit_profit_take_response",
            data={
                'request_id': request_id,
                'execution': execution,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_quality_request(self, event: Event):
        """Handle quality requests"""
        if not self.running:
            return
            
        agent = event.data.get('agent')
        
        if agent:
            scores = self.quality_scores.get(agent, {})
        else:
            scores = self.quality_scores
            
        response = Event(
            event_type="quality_response",
            data={
                'agent': agent,
                'scores': scores,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_reward_penalty_request(self, event: Event):
        """Handle reward/penalty requests"""
        if not self.running:
            return
            
        agent = event.data.get('agent')
        action = event.data.get('action')
        
        if action == 'reward':
            result = await self.apply_reward(agent)
        elif action == 'penalty':
            result = await self.apply_penalty(agent)
        else:
            result = {'status': 'unknown_action'}
            
        response = Event(
            event_type="reward_penalty_response",
            data={
                'agent': agent,
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def audit_execution(self, execution: Dict) -> Dict:
        """Audit a profit-taking execution"""
        # Extract metrics
        expected_price = execution.get('expected_price', 0)
        executed_price = execution.get('executed_price', 0)
        expected_size = execution.get('expected_size', 0)
        executed_size = execution.get('executed_size', 0)
        agent = execution.get('agent', 'unknown')
        
        # Calculate metrics
        profit_capture = executed_size / expected_size if expected_size > 0 else 0
        slippage = abs(executed_price - expected_price) / expected_price if expected_price > 0 else 0
        
        # Determine quality
        quality_score = 0
        if profit_capture >= self.config['profit_capture_target']:
            quality_score += 50
        else:
            quality_score += profit_capture / self.config['profit_capture_target'] * 50
            
        if slippage <= self.config['slippage_target']:
            quality_score += 50
        else:
            quality_score += max(0, 50 * (1 - (slippage - self.config['slippage_target']) / 0.02))
            
        # Determine grade
        if quality_score >= 90:
            grade = 'A'
        elif quality_score >= 80:
            grade = 'B'
        elif quality_score >= 70:
            grade = 'C'
        elif quality_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
            
        audit_result = {
            'execution_id': execution.get('id'),
            'profit_capture': profit_capture,
            'slippage': slippage,
            'quality_score': quality_score,
            'grade': grade,
            'agent': agent,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store audit result
        self.audit_results.append(audit_result)
        
        # Store quality score
        if agent not in self.quality_scores:
            self.quality_scores[agent] = {
                'scores': [],
                'average': 0,
                'grade': 'N/A'
            }
        self.quality_scores[agent]['scores'].append(quality_score)
        
        # Keep last 100 scores
        if len(self.quality_scores[agent]['scores']) > 100:
            self.quality_scores[agent]['scores'] = self.quality_scores[agent]['scores'][-100:]
            
        # Update average
        avg_score = statistics.mean(self.quality_scores[agent]['scores'])
        self.quality_scores[agent]['average'] = avg_score
        
        # Update grade
        if avg_score >= 90:
            self.quality_scores[agent]['grade'] = 'A'
        elif avg_score >= 80:
            self.quality_scores[agent]['grade'] = 'B'
        elif avg_score >= 70:
            self.quality_scores[agent]['grade'] = 'C'
        elif avg_score >= 60:
            self.quality_scores[agent]['grade'] = 'D'
        else:
            self.quality_scores[agent]['grade'] = 'F'
            
        return audit_result
        
    async def review_audits(self):
        """Review pending audits"""
        # Process audits that haven't been fully reviewed
        pending = [a for a in self.audit_results if not a.get('reviewed')]
        
        for audit in pending[:10]:
            # Mark as reviewed
            audit['reviewed'] = True
            audit['review_timestamp'] = datetime.now().isoformat()
            
            # Check if reward or penalty needed
            if audit['quality_score'] >= 80:
                await self.apply_reward(audit['agent'])
            elif audit['quality_score'] < 60:
                await self.apply_penalty(audit['agent'])
                
    async def update_quality_scores(self):
        """Update quality scores"""
        # Recalculate averages
        for agent, data in self.quality_scores.items():
            if data['scores']:
                avg_score = statistics.mean(data['scores'])
                data['average'] = avg_score
                
                # Update grade
                if avg_score >= 90:
                    data['grade'] = 'A'
                elif avg_score >= 80:
                    data['grade'] = 'B'
                elif avg_score >= 70:
                    data['grade'] = 'C'
                elif avg_score >= 60:
                    data['grade'] = 'D'
                else:
                    data['grade'] = 'F'
                    
                # Store in state
                await self.state_manager.set(f'quality_score_{agent}', data)
                
    async def apply_rewards_penalties(self):
        """Apply rewards and penalties"""
        for agent, data in self.quality_scores.items():
            if data['scores'] and len(data['scores']) >= self.config['min_trades_for_audit']:
                avg_score = data['average']
                
                if avg_score >= 80:
                    await self.apply_reward(agent)
                elif avg_score < 60:
                    await self.apply_penalty(agent)
                    
    async def apply_reward(self, agent: str) -> Dict:
        """Apply reward to an agent"""
        # In production, implement actual reward mechanism
        # For now, record reward
        
        reward = {
            'agent': agent,
            'amount': self.config['reward_factor'],
            'timestamp': datetime.now().isoformat()
        }
        self.reward_history.append(reward)
        
        # Store in state
        await self.state_manager.set(f'reward_{agent}', reward)
        
        logger.info(f"🏆 Reward applied to {agent}")
        
        return {'status': 'rewarded', 'agent': agent}
        
    async def apply_penalty(self, agent: str) -> Dict:
        """Apply penalty to an agent"""
        # In production, implement actual penalty mechanism
        # For now, record penalty
        
        penalty = {
            'agent': agent,
            'amount': self.config['penalty_factor'],
            'timestamp': datetime.now().isoformat()
        }
        self.penalty_history.append(penalty)
        
        # Store in state
        await self.state_manager.set(f'penalty_{agent}', penalty)
        
        logger.info(f"⚠️ Penalty applied to {agent}")
        
        return {'status': 'penalized', 'agent': agent}
        
    async def publish_audit_update(self):
        """Publish audit data update"""
        audit_data = {
            'total_audits': len(self.audit_results),
            'quality_scores': self.quality_scores,
            'reward_history': self.reward_history[-5:],
            'penalty_history': self.penalty_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="profit_taking_audit_update",
            data=audit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get profit taking auditor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_audits': len(self.audit_results),
            'quality_scores': len(self.quality_scores),
            'rewards_given': len(self.reward_history),
            'penalties_applied': len(self.penalty_history),
            'timestamp': datetime.now().isoformat()
        }
