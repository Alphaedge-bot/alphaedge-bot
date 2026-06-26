"""
AlphaEdge Agent 30 – Self-Evolving Architect
Proposes code improvements, CEO approves.
Grok AI: strategy upgrades only (max 10 calls/week)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SelfEvolvingArchitect:
    """Self-Evolving Architect – Proposes code improvements and upgrades"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "self_evolving"
        self.running = False
        
        # Evolution state
        self.proposals = []
        self.approved_changes = []
        self.rejected_changes = []
        
        # Grok AI integration
        self.grok_available = True
        self.grok_call_count = 0
        self.grok_max_calls = 10  # Max 10 calls/week
        self.grok_reset_time = datetime.now()
        
        # Change tracking
        self.code_version = "V13.0.5"
        self.upgrade_history = []
        
    async def start(self):
        """Start the self-evolving architect"""
        logger.info("Self-Evolving Architect starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("improvement_request", self.handle_improvement_request)
        await self.event_bus.subscribe("proposal_review_request", self.handle_proposal_review)
        await self.event_bus.subscribe("upgrade_approval", self.handle_upgrade_approval)
        
        # Start evolution cycle
        asyncio.create_task(self.run_evolution_cycle())
        
        logger.info("Self-Evolving Architect running")
        
    async def stop(self):
        """Stop the self-evolving architect"""
        self.running = False
        logger.info("Self-Evolving Architect stopped")
        
    async def run_evolution_cycle(self):
        """Run regular evolution cycle"""
        while self.running:
            try:
                # Generate improvement proposals
                await self.generate_proposals()
                
                # Review pending proposals
                await self.review_proposals()
                
                # Publish evolution update
                await self.publish_evolution_update()
                
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
                
            await asyncio.sleep(3600)  # Every hour
            
    async def handle_improvement_request(self, event: Event):
        """Handle improvement requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        area = event.data.get('area', 'strategy')
        
        logger.info(f"Improvement request: {request_id} ({area})")
        
        # Generate proposal
        proposal = await self.generate_proposal(area)
        
        # Store proposal
        self.proposals.append({
            'id': proposal['id'],
            'request_id': request_id,
            'proposal': proposal,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        })
        
        # Send response
        response = Event(
            event_type="improvement_proposal",
            data=proposal,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def generate_proposal(self, area: str) -> Dict:
        """Generate an improvement proposal"""
        # Simulate generating a proposal
        # In production, this would use Grok AI
        
        if area == 'strategy':
            proposal = {
                'id': f"prop_{datetime.now().timestamp()}",
                'type': 'strategy_upgrade',
                'area': area,
                'title': 'Enhanced Momentum Strategy',
                'description': 'Improved momentum calculation with volume weighting',
                'expected_improvement': random.uniform(5, 15),
                'risk_level': 'low',
                'implementation_steps': [
                    'Add volume_weighted_roc function',
                    'Update entry conditions',
                    'Backtest with new parameters'
                ]
            }
        elif area == 'optimization':
            proposal = {
                'id': f"prop_{datetime.now().timestamp()}",
                'type': 'parameter_optimization',
                'area': area,
                'title': 'TPS Threshold Optimization',
                'description': 'Fine-tune TPS thresholds based on market regimes',
                'expected_improvement': random.uniform(3, 10),
                'risk_level': 'low',
                'implementation_steps': [
                    'Analyze TPS performance by regime',
                    'Update threshold values',
                    'Test in dry run mode'
                ]
            }
        else:
            proposal = {
                'id': f"prop_{datetime.now().timestamp()}",
                'type': 'code_improvement',
                'area': area,
                'title': f'Code Optimization: {area.title()}',
                'description': f'Optimize {area} module for better performance',
                'expected_improvement': random.uniform(2, 8),
                'risk_level': 'low',
                'implementation_steps': [
                    f'Analyze {area} code',
                    'Implement improvements',
                    'Run tests'
                ]
            }
            
        return proposal
        
    async def review_proposals(self):
        """Review pending proposals"""
        for proposal in self.proposals:
            if proposal['status'] != 'pending':
                continue
                
            # Check if proposal violates core principles
            if await self.check_core_principles(proposal['proposal']):
                proposal['status'] = 'rejected'
                proposal['reason'] = 'Violates core principles'
                self.rejected_changes.append(proposal)
                continue
                
            # Check if upgrade only (no downgrades)
            if proposal['proposal']['type'] == 'downgrade':
                proposal['status'] = 'rejected'
                proposal['reason'] = 'Downgrades not allowed (Upgrade only policy)'
                self.rejected_changes.append(proposal)
                continue
                
            # Check if performance degradation
            if proposal['proposal'].get('expected_improvement', 0) < 0:
                proposal['status'] = 'rejected'
                proposal['reason'] = 'Would cause performance degradation'
                self.rejected_changes.append(proposal)
                continue
                
            # Proceed to CEO for approval
            await self.submit_to_ceo(proposal)
            
    async def check_core_principles(self, proposal: Dict) -> bool:
        """Check if proposal violates core principles"""
        # List of core principles that cannot be changed
        protected_areas = [
            'momentum', 'low_cap', 'price_action',
            'circuit_breakers', 'emergency_stop',
            'wallet_structure', 'fed_liquidity',
            'core_architecture', 'agent_hierarchy'
        ]
        
        for area in protected_areas:
            if area in proposal.get('area', '').lower():
                return True
                
        return False
        
    async def submit_to_ceo(self, proposal: Dict):
        """Submit proposal to CEO for approval"""
        proposal['status'] = 'pending_ceo'
        
        # Send to CEO
        ceo_event = Event(
            event_type="proposal_for_approval",
            data={
                'proposal_id': proposal['id'],
                'proposal': proposal['proposal'],
                'requester': self.agent_id,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target='ceo'
        )
        await self.event_bus.publish(ceo_event)
        
        logger.info(f"Proposal {proposal['id']} submitted to CEO")
        
    async def handle_proposal_review(self, event: Event):
        """Handle proposal review requests"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        
        # Find proposal
        proposal = None
        for p in self.proposals:
            if p['id'] == proposal_id:
                proposal = p
                break
                
        # Send response
        response = Event(
            event_type="proposal_review_response",
            data={
                'proposal_id': proposal_id,
                'proposal': proposal,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_upgrade_approval(self, event: Event):
        """Handle CEO approval of upgrades"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        approved = event.data.get('approved')
        reason = event.data.get('reason', '')
        
        # Find proposal
        for proposal in self.proposals:
            if proposal['id'] == proposal_id:
                if approved:
                    proposal['status'] = 'approved'
                    self.approved_changes.append(proposal)
                    self.code_version = f"V13.0.{len(self.approved_changes) + 5}"
                    
                    # Record upgrade
                    self.upgrade_history.append({
                        'proposal_id': proposal_id,
                        'version': self.code_version,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"Proposal {proposal_id} approved: {self.code_version}")
                    
                    # Implement change
                    await self.implement_upgrade(proposal)
                else:
                    proposal['status'] = 'rejected'
                    proposal['reason'] = reason
                    self.rejected_changes.append(proposal)
                    logger.info(f"Proposal {proposal_id} rejected: {reason}")
                break
                
    async def implement_upgrade(self, proposal: Dict):
        """Implement an approved upgrade"""
        # Simulate implementation
        logger.info(f"Implementing upgrade: {proposal['proposal']['title']}")
        
        # Update state
        await self.state_manager.set('code_version', self.code_version)
        await self.state_manager.set('last_upgrade', {
            'proposal_id': proposal['id'],
            'version': self.code_version,
            'timestamp': datetime.now().isoformat()
        })
        
    async def generate_proposals(self):
        """Auto-generate improvement proposals"""
        # Only generate if running and no pending proposals
        pending = [p for p in self.proposals if p['status'] in ['pending', 'pending_ceo']]
        if len(pending) > 5:
            return
            
        # Check if Grok AI is available
        if self.grok_available and self.grok_call_count < self.grok_max_calls:
            # Use Grok AI to generate proposals
            await self.use_grok_for_proposal()
        else:
            # Fallback to heuristic proposals
            await self.generate_heuristic_proposal()
            
    async def use_grok_for_proposal(self):
        """Use Grok AI to generate proposals"""
        # Check weekly limit
        if datetime.now() - self.grok_reset_time > timedelta(days=7):
            self.grok_call_count = 0
            self.grok_reset_time = datetime.now()
            
        if self.grok_call_count >= self.grok_max_calls:
            logger.warning("Grok AI call limit reached (10/week)")
            return
            
        # Simulate Grok AI call
        self.grok_call_count += 1
        
        # Generate proposal
        areas = ['strategy', 'optimization', 'code_improvement']
        area = random.choice(areas)
        proposal = await self.generate_proposal(area)
        
        # Store proposal
        self.proposals.append({
            'id': proposal['id'],
            'request_id': f"grok_{datetime.now().timestamp()}",
            'proposal': proposal,
            'status': 'pending',
            'source': 'grok_ai',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Grok AI proposal generated ({self.grok_call_count}/10)")
        
    async def generate_heuristic_proposal(self):
        """Generate heuristic-based proposals"""
        # Simple heuristic proposals
        if len(self.proposals) < 3:
            proposal = await self.generate_proposal('optimization')
            
            self.proposals.append({
                'id': proposal['id'],
                'request_id': f"heuristic_{datetime.now().timestamp()}",
                'proposal': proposal,
                'status': 'pending',
                'source': 'heuristic',
                'timestamp': datetime.now().isoformat()
            })
            
    async def publish_evolution_update(self):
        """Publish evolution data update"""
        evolution_data = {
            'code_version': self.code_version,
            'proposals': len(self.proposals),
            'approved_changes': len(self.approved_changes),
            'rejected_changes': len(self.rejected_changes),
            'pending_proposals': len([p for p in self.proposals if p['status'] == 'pending']),
            'grok_calls_used': self.grok_call_count,
            'grok_max_calls': self.grok_max_calls,
            'upgrade_history': self.upgrade_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="evolution_update",
            data=evolution_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get self-evolving architect status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'code_version': self.code_version,
            'total_proposals': len(self.proposals),
            'approved_changes': len(self.approved_changes),
            'pending_proposals': len([p for p in self.proposals if p['status'] == 'pending']),
            'grok_calls_used': self.grok_call_count,
            'grok_calls_remaining': self.grok_max_calls - self.grok_call_count,
            'timestamp': datetime.now().isoformat()
        }
