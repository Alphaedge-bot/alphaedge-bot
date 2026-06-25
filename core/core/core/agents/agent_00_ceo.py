"""
AlphaEdge Agent 00 – CEO (Supreme Override)
Strategic direction, goal tracking, conflict resolution
Override any agent, approve major decisions, executive summaries
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CEOAgent:
    """Supreme Override Agent – Final authority on all decisions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "ceo"
        self.running = False
        self.pending_approvals = {}
        self.executive_summary = {}
        
    async def start(self):
        """Start the CEO agent"""
        logger.info("CEO Agent starting...")
        self.running = True
        
        # Subscribe to critical events
        await self.event_bus.subscribe("decision_approval_request", self.handle_approval_request)
        await self.event_bus.subscribe("conflict_detected", self.handle_conflict)
        await self.event_bus.subscribe("emergency_alert", self.handle_emergency)
        await self.event_bus.subscribe("strategy_proposal", self.handle_strategy_proposal)
        
        logger.info("CEO Agent running")
        
    async def stop(self):
        """Stop the CEO agent"""
        self.running = False
        logger.info("CEO Agent stopped")
        
    async def handle_approval_request(self, event: Event):
        """Handle decision approval requests"""
        if not self.running:
            return
            
        decision = event.data.get('decision', {})
        decision_id = event.data.get('decision_id')
        
        logger.info(f"Approval request received: {decision_id}")
        
        # Evaluate decision
        approved, reason = await self.evaluate_decision(decision)
        
        # Send response
        response = Event(
            event_type="decision_approval_response",
            data={
                'decision_id': decision_id,
                'approved': approved,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def evaluate_decision(self, decision: Dict[str, Any]) -> tuple:
        """Evaluate if a decision should be approved"""
        # Check if decision violates core principles
        if decision.get('type') == 'entry':
            tps = decision.get('tps', 0)
            if tps < 82:
                return False, f"TPS {tps} below entry threshold (82)"
                
        # Check risk limits
        risk = decision.get('risk', 0)
        if risk > 0.7:
            return False, f"Risk score {risk} exceeds limit (0.7)"
            
        # Check drawdown limits
        drawdown = decision.get('drawdown', 0)
        if drawdown > 0.10:
            return False, f"Drawdown {drawdown*100:.1f}% exceeds 10% limit"
            
        # Check circuit breakers
        cb_status = await self.state_manager.get('circuit_breakers', {})
        if cb_status.get('active', False):
            return False, "Circuit breakers active"
            
        # Check Fed liquidity
        fed_score = await self.state_manager.get('fed_liquidity_score', 50)
        if fed_score < 40:
            return False, f"Fed liquidity score {fed_score} below 40"
            
        return True, "Approved"
        
    async def handle_conflict(self, event: Event):
        """Handle conflicts between agents"""
        if not self.running:
            return
            
        conflict = event.data
        logger.warning(f"Conflict detected: {conflict}")
        
        # Analyze conflict
        resolution = await self.resolve_conflict(conflict)
        
        # Broadcast resolution
        response = Event(
            event_type="conflict_resolution",
            data=resolution,
            source=self.agent_id
        )
        await self.event_bus.publish(response)
        
    async def resolve_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agents"""
        # Default resolution: prioritize risk management
        agent_a = conflict.get('agent_a')
        agent_b = conflict.get('agent_b')
        
        # Check which agent has higher priority
        priority_map = {
            'risk_guardian': 10,
            'circuit_breaker': 9,
            'fund_manager': 8,
            'proposer': 5,
            'opponent': 5
        }
        
        priority_a = priority_map.get(agent_a, 0)
        priority_b = priority_map.get(agent_b, 0)
        
        if priority_a > priority_b:
            winner = agent_a
        elif priority_b > priority_a:
            winner = agent_b
        else:
            # If equal, ask CEO override
            winner = 'ceo_override'
            
        return {
            'winner': winner,
            'resolution': f'Priority resolved: {winner} wins',
            'timestamp': datetime.now().isoformat()
        }
        
    async def handle_emergency(self, event: Event):
        """Handle emergency alerts"""
        if not self.running:
            return
            
        emergency = event.data
        severity = emergency.get('severity', 'high')
        
        logger.error(f"🚨 EMERGENCY: {emergency.get('message')} (Severity: {severity})")
        
        if severity in ['critical', 'high']:
            # Send emergency stop command
            stop_event = Event(
                event_type="emergency_stop",
                data={
                    'reason': emergency.get('message'),
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(stop_event)
            
    async def handle_strategy_proposal(self, event: Event):
        """Handle strategy upgrade proposals"""
        if not self.running:
            return
            
        proposal = event.data
        proposal_id = proposal.get('id')
        
        logger.info(f"Strategy proposal received: {proposal_id}")
        
        # Evaluate proposal
        approved, reason = await self.evaluate_strategy_proposal(proposal)
        
        response = Event(
            event_type="strategy_proposal_response",
            data={
                'proposal_id': proposal_id,
                'approved': approved,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def evaluate_strategy_proposal(self, proposal: Dict[str, Any]) -> tuple:
        """Evaluate if a strategy proposal should be approved"""
        # Check if upgrade only (no downgrades)
        if proposal.get('type') == 'downgrade':
            return False, "Downgrades not allowed (Upgrade only policy)"
            
        # Check if core principles are violated
        if proposal.get('violates_core_principles', False):
            return False, "Violates core principles"
            
        # Check if safety systems are compromised
        if proposal.get('compromises_safety', False):
            return False, "Compromises safety systems"
            
        # Check if performance degradation
        if proposal.get('performance_degradation', False):
            return False, "Would cause performance degradation"
            
        return True, "Strategy approved"
        
    async def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of bot status"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'status': 'operational',
            'agents': {
                'total': 72,
                'active': await self.get_active_agent_count(),
                'warm_standby': 7
            },
            'positions': await self.state_manager.get_all_positions(),
            'circuit_breakers': await self.state_manager.get('circuit_breakers', {}),
            'performance': await self.state_manager.get('performance', {}),
            'fed_liquidity': await self.state_manager.get('fed_liquidity_score', 50)
        }
        
        self.executive_summary = summary
        return summary
        
    async def get_active_agent_count(self) -> int:
        """Get count of active agents"""
        # This would query the event bus for active agents
        # Placeholder for now
        return 65
