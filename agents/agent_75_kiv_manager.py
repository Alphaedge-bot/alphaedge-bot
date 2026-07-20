"""
AlphaEdge Agent 75 – KIV Manager
Auto-tracks, prioritizes, and assigns KIV items
V13.0.7 – FULL UPDATE with All Items
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
        
        # Proposals storage (item_id → full proposal)
        self.proposals = {}
        
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
        
        # Initialize KIV items and proposals
        self._init_kiv_items()
        self._load_proposals()

    def _init_kiv_items(self):
        """Initialize KIV list with ALL items"""
        items = [
            # ============================================
            # P0 – Critical
            # ============================================
            {'id': 'KIV-037', 'title': 'Multi-sig Wallets', 'priority': 'P0', 'category': 'security', 
             'files': ['core/wallet_manager.py', 'config/config.yaml']},
            {'id': 'KIV-038', 'title': 'Kill Switch', 'priority': 'P0', 'category': 'security', 
             'files': ['agents/agent_49_circuit_breaker.py', 'scripts/emergency_stop.sh']},
            
            # ============================================
            # P1 – High
            # ============================================
            {'id': 'KIV-039', 'title': 'Strategy Correlation Culling', 'priority': 'P1', 'category': 'performance', 
             'files': ['agents/agent_57_performance_analyzer.py', 'agents/agent_56_optimizer_engine.py']},
            {'id': 'KIV-040', 'title': 'ATR-based Stop Loss', 'priority': 'P1', 'category': 'risk', 
             'files': ['agents/agent_18_risk_guardian.py']},
            {'id': 'KIV-041', 'title': 'True Zero Trust (mTLS)', 'priority': 'P1', 'category': 'security', 
             'files': ['agents/agent_38_zero_trust.py', 'core/mtls.py']},
            {'id': 'KIV-046', 'title': 'Agent Sharding', 'priority': 'P1', 'category': 'infrastructure', 
             'files': ['core/orchestrator.py']},
            {'id': 'KIV-047', 'title': 'Human-in-the-loop Withdrawals', 'priority': 'P1', 'category': 'security', 
             'files': ['agents/agent_72_command_interface.py']},
            {'id': 'KIV-049', 'title': 'Agent_30 Auto-Doc Generator', 'priority': 'P1', 'category': 'documentation', 
             'files': ['agents/agent_30_self_evolving.py']},
            {'id': 'KIV-051', 'title': 'Agent_74 AI Orchestrator', 'priority': 'P1', 'category': 'infrastructure', 
             'files': ['agents/agent_74_ai_orchestrator.py', 'core/ai_connector.py']},
            {'id': 'KIV-052', 'title': 'Agent_30 AI Query Enhancement', 'priority': 'P1', 'category': 'performance', 
             'files': ['agents/agent_30_self_evolving.py']},
            {'id': 'KIV-054', 'title': 'AI Response Validation', 'priority': 'P1', 'category': 'security', 
             'files': ['core/ai_validator.py', 'agents/agent_22_cross_validation.py']},
            {'id': 'KIV-061', 'title': 'Event Bus 2.0 Upgrade', 'priority': 'P1', 'category': 'infrastructure', 
             'files': ['core/event_bus.py', 'core/circuit_breaker.py', 'core/backpressure.py']},
            
            # ============================================
            # P2 – Medium
            # ============================================
            {'id': 'KIV-042', 'title': 'Malaysia Compliance Review', 'priority': 'P2', 'category': 'compliance', 
             'files': ['agents/agent_54_compliance.py']},
            {'id': 'KIV-043', 'title': 'Stablecoin Diversification', 'priority': 'P2', 'category': 'risk', 
             'files': ['core/stablecoin_manager.py', 'config/config.yaml']},
            {'id': 'KIV-044', 'title': 'Graduated Drawdown Ladder', 'priority': 'P2', 'category': 'risk', 
             'files': ['agents/agent_18_risk_guardian.py']},
            {'id': 'KIV-050', 'title': 'Agent_76 Compliance Auditor', 'priority': 'P2', 'category': 'compliance', 
             'files': ['agents/agent_76_compliance_auditor.py']},
            {'id': 'KIV-053', 'title': 'AI Cost Management', 'priority': 'P2', 'category': 'infrastructure', 
             'files': ['core/ai_cost_tracker.py', 'config/config.yaml']},
            
            # ============================================
            # P3 – Low
            # ============================================
            {'id': 'KIV-045', 'title': 'Public Digest Sanitization', 'priority': 'P3', 'category': 'documentation', 
             'files': ['agents/agent_50_marketing.py']},
        ]
        
        for item in items:
            item['status'] = 'pending'
            item['assigned_to'] = self._auto_assign(item)
            item['created_at'] = datetime.now().isoformat()
            item['deadline'] = self._calculate_deadline(item['priority'])
            self.kiv_master['pending'].append(item)

    def _load_proposals(self):
        """Load full proposal details for ALL KIV items"""
        self.proposals = {
            # ============================================
            # P0 – Critical
            # ============================================
            'KIV-037': {
                'title': 'Multi-sig Wallets',
                'description': 'Implement 3-of-5 multi-sig for Wallet 1 with Gnosis Safe or Squads. Keys: 2 bot-held, 2 user-held, 1 emergency recovery.',
                'implementation': 'core/wallet_manager.py, config/config.yaml',
                'success_metrics': {'theft_risk': '80% reduction'},
                'estimated_time': '2 weeks',
                'risk': 'Low'
            },
            'KIV-038': {
                'title': 'Kill Switch',
                'description': 'Hardware + software kill switch to halt bot instantly. Physical button + Telegram command.',
                'implementation': 'agents/agent_49_circuit_breaker.py, scripts/emergency_stop.sh',
                'success_metrics': {'response_time': '<500ms'},
                'estimated_time': '1 week',
                'risk': 'Low'
            },
            
            # ============================================
            # P1 – High
            # ============================================
            'KIV-039': {
                'title': 'Strategy Correlation Culling',
                'description': 'Reduce 312 strategies to top 50 by correlation analysis. Disable strategies with >0.7 correlation to lower-performing one.',
                'implementation': 'agents/agent_57_performance_analyzer.py, agents/agent_56_optimizer_engine.py',
                'success_metrics': {'overfitting': '60% reduction'},
                'estimated_time': '1 week',
                'risk': 'Medium'
            },
            'KIV-040': {
                'title': 'ATR-based Stop Loss',
                'description': 'Replace fixed percentage stop loss with ATR-based dynamic SL. Formula: SL = 2.5 × ATR(14) with tier cap.',
                'implementation': 'agents/agent_18_risk_guardian.py',
                'success_metrics': {'noise_stop_outs': '40% reduction'},
                'estimated_time': '3 days',
                'risk': 'Low'
            },
            'KIV-041': {
                'title': 'True Zero Trust (mTLS)',
                'description': 'Implement mTLS + behavioral anomaly detection between all agents. Agent deviating from baseline = quarantined.',
                'implementation': 'agents/agent_38_zero_trust.py, core/mtls.py',
                'success_metrics': {'compromise_risk': '90% reduction'},
                'estimated_time': '2 weeks',
                'risk': 'Medium'
            },
            'KIV-046': {
                'title': 'Agent Sharding',
                'description': 'Group 72 agents into 5-7 pods by function (Data, Execution, Risk, etc.) with pod-level coordinators.',
                'implementation': 'core/orchestrator.py',
                'success_metrics': {'coordination_complexity': 'Reduced'},
                'estimated_time': '3 weeks',
                'risk': 'High'
            },
            'KIV-047': {
                'title': 'Human-in-the-loop Withdrawals',
                'description': 'Require human approval for withdrawals >$1,000 or >10% balance. 24-hour time-lock for large withdrawals.',
                'implementation': 'agents/agent_72_command_interface.py',
                'success_metrics': {'theft_risk': 'Additional 50% reduction'},
                'estimated_time': '1 week',
                'risk': 'Low'
            },
            'KIV-049': {
                'title': 'Agent_30 Auto-Doc Generator',
                'description': 'Agent_30 reads code and auto-generates master design, workflow, user guide. Ensures docs match code.',
                'implementation': 'agents/agent_30_self_evolving.py',
                'success_metrics': {'doc_accuracy': '100%'},
                'estimated_time': '2 days',
                'risk': 'Low'
            },
            'KIV-051': {
                'title': 'Agent_74 AI Orchestrator',
                'description': 'Universal AI connector for Kimi k3, OpenAI, Claude, DeepSeek. V13 remains master controller — AI advisory only.',
                'implementation': 'agents/agent_74_ai_orchestrator.py, core/ai_connector.py',
                'success_metrics': {'ai_response_time': '<2s'},
                'estimated_time': '2 weeks',
                'risk': 'Medium'
            },
            'KIV-052': {
                'title': 'Agent_30 AI Query Enhancement',
                'description': 'Self-Evolving can request AI code review, strategy design, and architecture suggestions. 4-layer validation.',
                'implementation': 'agents/agent_30_self_evolving.py',
                'success_metrics': {'code_quality': 'Improved'},
                'estimated_time': '3 days',
                'risk': 'Low'
            },
            'KIV-054': {
                'title': 'AI Response Validation',
                'description': '4-layer validation: schema check → cross-validation (Agent_22) → Risk Guardian (Agent_18) → Human veto (>$5,000).',
                'implementation': 'core/ai_validator.py, agents/agent_22_cross_validation.py',
                'success_metrics': {'hallucination_risk': 'Eliminated'},
                'estimated_time': '3 days',
                'risk': 'Low'
            },
            'KIV-061': {
                'title': 'Event Bus 2.0 Upgrade',
                'description': 'Replace single-queue event bus with 3-tier priority system (critical/normal/background), per-agent-pair circuit breakers, 3-level backpressure degradation, survival mode, latency tracking (p50/p95/p99), event replay capability, instant rollback.',
                'implementation': 'core/event_bus.py (REPLACE), core/circuit_breaker.py (NEW), core/backpressure.py (NEW), tests/test_event_bus.py (REPLACE), tests/test_circuit_breaker.py (NEW), main.py (MINOR)',
                'success_metrics': {
                    'p95_latency': '<50ms (was 180-400ms)',
                    'crash_cascades': '0 (was 3/month)',
                    'queue_memory': '<300MB (was 1.2-2.1GB)',
                    'kill_switch_response': '<500ms (was 4.2s)',
                    'agent_capacity': '150+ (was 80)'
                },
                'estimated_time': '3 weeks',
                'risk': 'Medium',
                'rollback': 'cp core/event_bus.py.backup core/event_bus.py'
            },
            
            # ============================================
            # P2 – Medium
            # ============================================
            'KIV-042': {
                'title': 'Malaysia Compliance Review',
                'description': 'Review and implement Malaysia Securities Commission requirements. Register as Technology Service Provider if managing external capital.',
                'implementation': 'agents/agent_54_compliance.py',
                'success_metrics': {'regulatory_risk': 'Eliminated'},
                'estimated_time': '1 week',
                'risk': 'Low'
            },
            'KIV-043': {
                'title': 'Stablecoin Diversification',
                'description': 'Diversify stablecoins: USDC (60%) + USDT (25%) + DAI (10%) + LUSD (5%). Add issuer freeze monitoring.',
                'implementation': 'core/stablecoin_manager.py, config/config.yaml',
                'success_metrics': {'stablecoin_risk': '70% reduction'},
                'estimated_time': '3 days',
                'risk': 'Low'
            },
            'KIV-044': {
                'title': 'Graduated Drawdown Ladder',
                'description': 'Define specific actions at 10% (reduce size 50%), 15% (liquidate 80% to USDC), 20% (full liquidation, cooling period).',
                'implementation': 'agents/agent_18_risk_guardian.py',
                'success_metrics': {'crisis_clarity': '100%'},
                'estimated_time': '2 days',
                'risk': 'Low'
            },
            'KIV-050': {
                'title': 'Agent_76 Compliance Auditor',
                'description': 'Dedicated agent for continuous Malaysia compliance monitoring. Alerts on regulatory changes.',
                'implementation': 'agents/agent_76_compliance_auditor.py',
                'success_metrics': {'compliance_risk': 'Eliminated'},
                'estimated_time': '3 days',
                'risk': 'Low'
            },
            'KIV-053': {
                'title': 'AI Cost Management',
                'description': 'Daily spend cap ($50/day per bot), auto-fallback to cheaper provider, real-time cost tracking dashboard.',
                'implementation': 'core/ai_cost_tracker.py, config/config.yaml',
                'success_metrics': {'cost_overrun': '0'},
                'estimated_time': '2 days',
                'risk': 'Low'
            },
            
            # ============================================
            # P3 – Low
            # ============================================
            'KIV-045': {
                'title': 'Public Digest Sanitization',
                'description': 'Remove sensitive info from public digest. Add 20% decoy signals to poison adversary models.',
                'implementation': 'agents/agent_50_marketing.py',
                'success_metrics': {'adversary_reverse_engineering': 'Reduced'},
                'estimated_time': '1 week',
                'risk': 'Low'
            },
            
            # ============================================
            # COMPLETED ITEMS (for reference)
            # ============================================
            'KIV-014': {
                'title': 'Hysteresis Buffer',
                'description': '3-tick buffer before exit. Resets counter on momentum recovery.',
                'implementation': 'agents/agent_69_momentum_rotator.py',
                'completed': True
            },
            'KIV-015': {
                'title': 'Liquidity Filter',
                'description': 'Min 24h volume $500K, min order book depth $50K, max spread 0.5%.',
                'implementation': 'agents/agent_63_profit_taking_executor.py',
                'completed': True
            },
            'KIV-019': {
                'title': 'Order Book Depth Check',
                'description': 'Depth must be 2x position size, max slippage 2%.',
                'implementation': 'agents/agent_18_risk_guardian.py',
                'completed': True
            },
            'KIV-026': {
                'title': 'Dynamic Kelly',
                'description': 'Size = Kelly% × RegimeMultiplier × ConfidenceMultiplier',
                'implementation': 'agents/agent_62_position_sizer.py',
                'completed': True
            },
            'KIV-027': {
                'title': 'Slippage Killer',
                'description': '40% market + 60% TWAP for micro-caps. SG VPS proxy for <15ms latency.',
                'implementation': 'agents/agent_23_execution_sniper.py, agents/agent_25_intent_abstractor.py',
                'completed': True
            },
            'KIV-028': {
                'title': 'Let Winners Run',
                'description': 'TPS ≥85 for 3 days + MCDX Golden Cross → Remove TP3/TP4, trail stop only.',
                'implementation': 'agents/agent_60_profit_optimizer.py, agents/agent_70_early_exit_blocker.py',
                'completed': True
            },
            'KIV-032': {
                'title': 'Fractional Kelly',
                'description': 'Quarter-Kelly (25% of full Kelly). Micro-caps capped at 2-4%.',
                'implementation': 'agents/agent_62_position_sizer.py',
                'completed': True
            },
            'KIV-033': {
                'title': 'RPC Hedged Requests',
                'description': '15ms staggered offset, Jito SG + Helius SG multiplexed requests.',
                'implementation': 'core/rpc_manager.py',
                'completed': True
            },
            'KIV-034': {
                'title': 'Capital Siloing Matrix',
                'description': '20% pre-allocation to active chains. Chain-Regime Index based on volume.',
                'implementation': 'agents/agent_65_capital_allocator.py',
                'completed': True
            },
            'KIV-035': {
                'title': 'Dynamic Jito Tip Scaling',
                'description': '75th percentile of last 5 slots. Atomic fallback with 1.2x scaling.',
                'implementation': 'agents/agent_31_solana_tx.py',
                'completed': True
            },
            'KIV-036': {
                'title': 'Sandwich Isolation Guard',
                'description': 'Strict Token Ledger Account Checks, minimum output verification, atomic failure on manipulation.',
                'implementation': 'agents/agent_63_profit_taking_executor.py',
                'completed': True
            },
            'KIV-048': {
                'title': 'Agent_75 KIV Manager',
                'description': 'Auto-tracks, prioritizes, and assigns KIV items. Stores full proposal details.',
                'implementation': 'agents/agent_75_kiv_manager.py',
                'completed': True
            }
        }

    def _auto_assign(self, item: Dict) -> str:
        return self.assignment_rules.get(item.get('category', 'infrastructure'), 'agent_30_self_evolving')

    def _calculate_deadline(self, priority: str) -> str:
        days = self.priority_matrix.get(priority, {}).get('days', 30)
        return (datetime.now() + timedelta(days=days)).isoformat()

    async def get_proposal(self, item_id: str) -> Optional[Dict]:
        """Get full proposal details for an item"""
        return self.proposals.get(item_id)

    async def start(self):
        """Start KIV Manager"""
        self.running = True
        await self.state_manager.set('kiv_master', self.kiv_master)
        await self.state_manager.set('kiv_proposals', self.proposals)
        logger.info(f"📋 KIV Manager started: {len(self.kiv_master['pending'])} items pending")
        
        await self.event_bus.subscribe("kiv_status", self.handle_kiv_status)
        await self.event_bus.subscribe("kiv_complete", self.handle_kiv_complete)
        await self.event_bus.subscribe("kiv_proposal", self.handle_kiv_proposal)

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

    async def handle_kiv_proposal(self, event: Event):
        """Handle KIV proposal requests"""
        if not self.running:
            return
        
        item_id = event.data.get('item_id')
        proposal = await self.get_proposal(item_id)
        
        response = Event(
            event_type="kiv_proposal_response",
            data={
                'item_id': item_id,
                'proposal': proposal,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)

    async def get_status(self) -> Dict[str, Any]:
        """Get KIV Manager status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending': len(self.kiv_master['pending']),
            'in_progress': len(self.kiv_master['in_progress']),
            'completed': len(self.kiv_master['completed']),
            'deferred': len(self.kiv_master['deferred']),
            'proposals_loaded': len(self.proposals),
            'timestamp': datetime.now().isoformat()
        }
