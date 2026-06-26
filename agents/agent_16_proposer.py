"""
AlphaEdge Agent 16 – Proposer (Bullish)
Argues FOR entry using Ticker Performance Score (TPS)
Technical/on-chain/macro evidence required
3 debate rounds with Opponent
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class Proposer:
    """Proposer – Argues FOR entry with TPS and supporting evidence"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "proposer"
        self.running = False
        
        # Debate state
        self.active_debates = {}
        self.proposal_history = []
        
        # Required TPS threshold
        self.tps_threshold = 82
        
    async def start(self):
        """Start the proposer agent"""
        logger.info("Proposer starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("entry_proposal_request", self.handle_entry_proposal)
        await self.event_bus.subscribe("debate_response", self.handle_debate_response)
        await self.event_bus.subscribe("debate_round_end", self.handle_debate_round_end)
        
        logger.info("Proposer running")
        
    async def stop(self):
        """Stop the proposer agent"""
        self.running = False
        logger.info("Proposer stopped")
        
    async def handle_entry_proposal(self, event: Event):
        """Handle entry proposal requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        proposal_id = event.data.get('proposal_id')
        
        logger.info(f"Entry proposal requested for {token}")
        
        # Gather evidence
        evidence = await self.gather_evidence(token)
        
        # Check if TPS meets threshold
        tps = evidence.get('tps', 0)
        
        if tps >= self.tps_threshold:
            # Create proposal
            proposal = {
                'id': proposal_id,
                'token': token,
                'decision': 'entry',
                'evidence': evidence,
                'tps': tps,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store proposal
            self.proposal_history.append(proposal)
            
            # Send proposal for debate
            debate_event = Event(
                event_type="debate_start",
                data={
                    'proposal_id': proposal_id,
                    'proposal': proposal,
                    'round': 1,
                    'max_rounds': 3,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(debate_event)
            
            logger.info(f"Proposal {proposal_id} sent for debate")
        else:
            # TPS too low, reject
            response = Event(
                event_type="entry_proposal_response",
                data={
                    'proposal_id': proposal_id,
                    'approved': False,
                    'reason': f'TPS {tps} below threshold {self.tps_threshold}',
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id,
                target=event.source
            )
            await self.event_bus.publish(response)
            
    async def gather_evidence(self, token: str) -> Dict[str, Any]:
        """Gather evidence for entry proposal"""
        # Get data from various sources
        tps = await self.state_manager.get(f'tps_{token}', 0)
        
        # Get technical indicators
        technical = await self.state_manager.get('technical_indicators', {})
        
        # Get on-chain metrics
        onchain = await self.state_manager.get(f'onchain_metrics_{token}', {})
        
        # Get macro conditions
        macro = await self.state_manager.get('macro_score', 50)
        
        # Get sentiment
        sentiment = await self.state_manager.get('sentiment_score', 50)
        
        # Build evidence
        evidence = {
            'tps': tps,
            'technical': {
                'rsi': technical.get('rsi', 50),
                'macd': technical.get('macd', {}),
                'emas': technical.get('emas', {})
            },
            'onchain': {
                'mvrv': onchain.get('mvrv', 0),
                'nupl': onchain.get('nupl', 0),
                'exchange_netflow': onchain.get('exchange_netflow', 0)
            },
            'macro': macro,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        }
        
        return evidence
        
    async def handle_debate_response(self, event: Event):
        """Handle debate responses from Opponent"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        round_num = event.data.get('round')
        opponent_args = event.data.get('arguments')
        
        logger.info(f"Debate response received for {proposal_id} round {round_num}")
        
        # Prepare rebuttal
        rebuttal = await self.prepare_rebuttal(proposal_id, opponent_args)
        
        # Send rebuttal
        rebuttal_event = Event(
            event_type="debate_rebuttal",
            data={
                'proposal_id': proposal_id,
                'round': round_num,
                'rebuttal': rebuttal,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(rebuttal_event)
        
    async def prepare_rebuttal(self, proposal_id: str, opponent_args: Dict) -> Dict:
        """Prepare rebuttal to opponent's arguments"""
        # Find proposal
        proposal = None
        for p in self.proposal_history:
            if p.get('id') == proposal_id:
                proposal = p
                break
                
        if not proposal:
            return {'rebuttal': 'Proposal not found'}
            
        # Prepare counter-arguments
        rebuttal = {
            'strengths': [],
            'counter_points': [],
            'conclusion': 'entry_justified'
        }
        
        # Counter each opponent point
        for arg in opponent_args.get('points', []):
            if 'TPS' in arg:
                rebuttal['counter_points'].append(
                    f"TPS {proposal['tps']} exceeds threshold {self.tps_threshold}"
                )
            elif 'risk' in arg.lower():
                rebuttal['counter_points'].append(
                    "Risk is within acceptable limits (drawdown <5%)"
                )
            elif 'macro' in arg.lower():
                rebuttal['counter_points'].append(
                    f"Macro conditions support entry (score: {proposal['evidence']['macro']})"
                )
                
        return rebuttal
        
    async def handle_debate_round_end(self, event: Event):
        """Handle debate round end"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        round_num = event.data.get('round')
        result = event.data.get('result')
        
        logger.info(f"Debate round {round_num} ended for {proposal_id}: {result}")
        
        # If this was the final round, publish final decision
        if round_num >= 3:
            await self.publish_final_decision(proposal_id, result)
            
    async def publish_final_decision(self, proposal_id: str, debate_result: str):
        """Publish final decision based on debate results"""
        # Find proposal
        proposal = None
        for p in self.proposal_history:
            if p.get('id') == proposal_id:
                proposal = p
                break
                
        if not proposal:
            return
            
        # Determine if entry is approved
        approved = debate_result.get('winner') == 'proposer'
        
        # Publish decision
        decision_event = Event(
            event_type="entry_proposal_response",
            data={
                'proposal_id': proposal_id,
                'approved': approved,
                'token': proposal['token'],
                'tps': proposal['tps'],
                'evidence': proposal['evidence'],
                'debate_result': debate_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(decision_event)
        
        logger.info(f"Final decision for {proposal_id}: {'APPROVED' if approved else 'REJECTED'}")
        
    async def get_status(self) -> Dict[str, Any]:
        """Get proposer status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_debates': len(self.active_debates),
            'proposals_made': len(self.proposal_history),
            'timestamp': datetime.now().isoformat()
        }
