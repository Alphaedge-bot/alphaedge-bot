"""
AlphaEdge Agent 75 – KIV Manager
Auto-tracks, prioritizes, and assigns KIV items
V13.0.7 – NEW AGENT
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class KIVManager:
    """KIV Manager – Auto-tracks and assigns improvement items"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "kiv_manager"
        self.running = False
        
        # KIV Master List
        self.kiv_master = {
            'pending': [],
            'in_progress': [],
            'completed': [],
            'deferred': []
        }
        
        # Assignment rules: category → agent
        self.assignment_rules = {
            'security': 'agent_38_zero_trust',
            'risk': 'agent_18_risk_guardian',
            'performance': 'agent_56_optimizer_engine',
            'documentation': 'agent_30_self_evolving',
            'infrastructure': 'agent_45_redundancy_manager',
            'compliance': 'agent_54_compliance',
            'execution': 'agent_63_profit_taking_executor'
        }
        
        # Priority matrix
        self.priority_matrix = {
            'P0': {'days': 7, 'severity': 'critical'},
            'P1': {'days': 14, 'severity': 'high'},
            'P2': {'days': 30, 'severity': 'medium'},
            'P3': {'days': 60, 'severity': 'low'}
        }
        
        # Initialize KIV items
        self._init_kiv_items()

    def _init_kiv_items(self):
        """Initialize KIV list from master design"""
        items = [
            # P0 – Critical
            {'id': 'KIV-037', 'title': 'Multi-sig Wallets', 'priority': 'P0', 'category': 'security', 'files': ['core/wallet_manager.py', 'config/config.yaml']},
            {'id': 'KIV-038', 'title': 'Kill Switch', 'priority': 'P0', 'category': 'security', 'files': ['agents/agent_49_circuit_breaker.py', 'scripts/emergency_stop.sh']},
            # P1 – High
            {'id': 'KIV-039', 'title': 'Strategy Correlation Culling', 'priority': 'P1', 'category': 'performance', 'files': ['agents/agent_57_performance_analyzer.py', 'agents/agent_56_optimizer_engine.py']},
            {'id': 'KIV-041', 'title': 'True Zero Trust (mTLS)', 'priority': 'P1', 'category': 'security', 'files': ['agents/agent_38_zero_trust.py', 'core/mtls.py']},
            {'id': 'KIV-046', 'title': 'Agent Sharding', 'priority': 'P1', 'category': 'infrastructure', 'files': ['core/orchestrator.py']},
            {'id': 'KIV-047', 'title': 'Human-in-the-loop Withdrawals', 'priority': 'P1', 'category': 'security', 'files': ['agents/agent_72_command_interface.py']},
            {'id': 'KIV-061', 'title': 'Event Bus 2.0 Upgrade', 'priority': 'P1', 'category': 'infrastructure', 'files': ['core/event_bus.py', 'core/circuit_breaker.py', 'core/backpressure.py']},
            # P2 – Medium
            {'id': 'KIV-042', 'title': 'Malaysia Compliance Review', 'priority': 'P2', 'category': 'compliance', 'files': ['agents/agent_54_compliance.py']},
            {'id': 'KIV-043', 'title': 'Stablecoin Diversification', 'priority': 'P2', 'category': 'risk', 'files': ['core/stablecoin_manager.py', 'config/config.yaml']},
            {'id': 'KIV-044', 'title': 'Graduated Drawdown Ladder', 'priority': 'P2', 'category': 'risk', 'files': ['agents/agent_18_risk_guardian.py']},
            {'id': 'KIV-050', 'title': 'Agent_76 Compliance Auditor', 'priority': 'P2', 'category': 'compliance', 'files': ['agents/agent_76_compliance_auditor.py']},
            # P3 – Low
            {'id': 'KIV-045', 'title': 'Public Digest Sanitization', 'priority': 'P3', 'category': 'documentation', 'files': ['agents/agent_50_marketing.py']},
            # Agent Items
            {'id': 'KIV-048', 'title': 'Agent_75 KIV Manager', 'priority': 'P1', 'category': 'infrastructure', 'files': ['agents/agent_75_kiv_manager.py']},
            {'id': 'KIV-049', 'title': 'Agent_30 Auto-Doc Generator', 'priority': 'P1', 'category': 'documentation', 'files': ['agents/agent_30_self_evolving.py']},
            # AI Items
            {'id': 'KIV-051', 'title': 'Agent_74 AI Orchestrator', 'priority': 'P1', 'category': 'infrastructure', 'files': ['agents/agent_74_ai_orchestrator.py', 'core/ai_connector.py']},
            {'id': 'KIV-052', 'title': 'Agent_30 AI Query Enhancement', 'priority': 'P1', 'category': 'performance', 'files': ['agents/agent_30_self_evolving.py']},
            {'id': 'KIV-053', 'title': 'AI Cost Management', 'priority': 'P2', 'category': 'infrastructure', 'files': ['core/ai_cost_tracker.py', 'config/config.yaml']},
            {'id': 'KIV-054', 'title': 'AI Response Validation', 'priority': 'P1', 'category': 'security', 'files': ['core/ai_validator.py', 'agents/agent_22_cross_validation.py']},
        ]
        
        for item in items:
            item['status'] = 'pending'
            item['assigned_to'] = self._auto_assign(item)
            item['created_at'] = datetime.now().isoformat()
            item['deadline'] = self._calculate_deadline(item['priority'])
            self.kiv_master['pending'].append(item)

    def _auto_assign(self, item: Dict) -> str:
        return self.assignment_rules.get(item.get('category', 'infrastructure'), 'agent_30_self_evolving')

    def _calculate_deadline(self, priority: str) -> str:
        days = self.priority_matrix.get(priority, {}).get('days', 30)
        return (datetime.now() + timedelta(days=days)).isoformat()

    async def start(self):
        """Start KIV Manager"""
        self.running = True
        # Save state
        await self.state_manager.set('kiv_master', self.kiv_master)
        logger.info(f"📋 KIV Manager started: {len(self.kiv_master['pending'])} items pending")
        
        # Subscribe to events
        await self.event_bus.subscribe("kiv_status", self.handle_kiv_status)
        await self.event_bus.subscribe("kiv_complete", self.handle_kiv_complete)

    async def stop(self):
        """Stop KIV Manager"""
        self.running = False
        logger.info("KIV Manager stopped")

    async def handle_kiv_status(self, event: Event):
        """Handle KIV status requests"""
        if not self.running:
            return
        
        response = Event(
            event_type="kiv_status_response",
            data={
                'pending': len(self.kiv_master['pending']),
                'in_progress': len(self.kiv_master['in_progress']),
                'completed': len(self.kiv_master['completed']),
                'deferred': len(self.kiv_master['deferred']),
                'pending_items': self.kiv_master['pending'],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)

    async def handle_kiv_complete(self, event: Event):
        """Handle KIV complete requests"""
        if not self.running:
            return
        
        item_id = event.data.get('item_id')
        for i, item in enumerate(self.kiv_master['pending']):
            if item['id'] == item_id:
                item['status'] = 'completed'
                item['completed_at'] = datetime.now().isoformat()
                self.kiv_master['pending'].pop(i)
                self.kiv_master['completed'].append(item)
                await self.state_manager.set('kiv_master', self.kiv_master)
                logger.info(f"✅ KIV item completed: {item_id}")
                break

    async def get_status(self) -> Dict[str, Any]:
        """Get KIV Manager status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending': len(self.kiv_master['pending']),
            'in_progress': len(self.kiv_master['in_progress']),
            'completed': len(self.kiv_master['completed']),
            'deferred': len(self.kiv_master['deferred']),
            'timestamp': datetime.now().isoformat()
        }
