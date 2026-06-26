"""
AlphaEdge Agent 21 – Consensus Engine
3/4 or 4/5 required on critical decisions
Aggregates votes from multiple agents
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """Consensus Engine – Aggregates votes and reaches consensus on decisions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "consensus"
        self.running = False
        
        # Consensus state
        self.active_votes = {}
        self.vote_history = []
        self.consensus_threshold = 0.75  # 75% required for consensus
        
        # Agent voting weights
        self.voting_weights = {
            'ceo': 1.5,
            'risk_guardian': 1.3,
            'fund_manager': 1.2,
            'proposer': 1.0,
            'opponent': 1.0,
            'technical': 1.0,
            'macro': 1.0,
            'sentiment': 0.8,
            'onchain': 0.8
        }
        
    async def start(self):
        """Start the consensus engine"""
        logger.info("Consensus Engine starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("vote_request", self.handle_vote_request)
        await self.event_bus.subscribe("vote_cast", self.handle_vote_cast)
        await self.event_bus.subscribe("consensus_request", self.handle_consensus_request)
        
        # Start monitoring cycle
        asyncio.create_task(self.run_consensus_cycle())
        
        logger.info("Consensus Engine running")
        
    async def stop(self):
        """Stop the consensus engine"""
        self.running = False
        logger.info("Consensus Engine stopped")
        
    async def run_consensus_cycle(self):
        """Run regular consensus monitoring"""
        while self.running:
            try:
                # Check for expired votes
                await self.check_expired_votes()
                
                # Process pending votes
                await self.process_pending_votes()
                
                # Publish consensus update
                await self.publish_consensus_update()
                
            except Exception as e:
                logger.error(f"Consensus cycle error: {e}")
                
            await asyncio.sleep(30)  # Every 30 seconds
            
    async def handle_vote_request(self, event: Event):
        """Handle vote requests"""
        if not self.running:
            return
            
        vote_id = event.data.get('vote_id')
        proposal = event.data.get('proposal')
        agents = event.data.get('agents', [])
        deadline = event.data.get('deadline', 60)  # 60 seconds default
        
        logger.info(f"Vote requested: {vote_id}")
        
        # Create vote
        vote = {
            'id': vote_id,
            'proposal': proposal,
            'agents': agents,
            'votes': {},
            'deadline': datetime.now().timestamp() + deadline,
            'status': 'active',
            'timestamp': datetime.now().isoformat()
        }
        
        self.active_votes[vote_id] = vote
        
        # Request votes from agents
        for agent in agents:
            vote_event = Event(
                event_type="vote_request",
                data={
                    'vote_id': vote_id,
                    'proposal': proposal,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id,
                target=agent
            )
            await self.event_bus.publish(vote_event)
            
        logger.info(f"Vote {vote_id} sent to {len(agents)} agents")
        
    async def handle_vote_cast(self, event: Event):
        """Handle votes cast by agents"""
        if not self.running:
            return
            
        vote_id = event.data.get('vote_id')
        agent = event.source
        decision = event.data.get('decision')
        confidence = event.data.get('confidence', 0.5)
        
        if vote_id not in self.active_votes:
            logger.warning(f"Vote {vote_id} not found")
            return
            
        # Record vote
        self.active_votes[vote_id]['votes'][agent] = {
            'decision': decision,
            'confidence': confidence,
            'weight': self.voting_weights.get(agent, 1.0),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Vote cast: {agent} voted {decision} on {vote_id}")
        
        # Check if consensus reached
        await self.check_consensus(vote_id)
        
    async def check_consensus(self, vote_id: str):
        """Check if consensus has been reached"""
        vote = self.active_votes.get(vote_id)
        if not vote:
            return
            
        votes = vote['votes']
        total_weight = 0
        approve_weight = 0
        reject_weight = 0
        
        for agent, data in votes.items():
            weight = data['weight']
            total_weight += weight
            
            if data['decision'] == 'approve':
                approve_weight += weight
            elif data['decision'] == 'reject':
                reject_weight += weight
                
        if total_weight == 0:
            return
            
        approve_ratio = approve_weight / total_weight
        reject_ratio = reject_weight / total_weight
        
        # Check if consensus reached
        if approve_ratio >= self.consensus_threshold:
            vote['status'] = 'approved'
            await self.finalize_vote(vote_id, 'approved')
        elif reject_ratio >= self.consensus_threshold:
            vote['status'] = 'rejected'
            await self.finalize_vote(vote_id, 'rejected')
            
    async def finalize_vote(self, vote_id: str, result: str):
        """Finalize a vote"""
        vote = self.active_votes.get(vote_id)
        if not vote:
            return
            
        # Record in history
        history_entry = {
            'vote_id': vote_id,
            'proposal': vote['proposal'],
            'result': result,
            'votes': vote['votes'],
            'timestamp': datetime.now().isoformat()
        }
        self.vote_history.append(history_entry)
        
        # Remove from active votes
        self.active_votes.pop(vote_id)
        
        # Publish result
        result_event = Event(
            event_type="vote_result",
            data={
                'vote_id': vote_id,
                'result': result,
                'proposal': vote['proposal'],
                'votes': vote['votes'],
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(result_event)
        
        logger.info(f"Vote {vote_id} finalized: {result}")
        
    async def check_expired_votes(self):
        """Check and expire old votes"""
        current_time = datetime.now().timestamp()
        
        for vote_id, vote in list(self.active_votes.items()):
            if current_time > vote['deadline']:
                # Vote expired
                vote['status'] = 'expired'
                await self.finalize_vote(vote_id, 'expired')
                
    async def process_pending_votes(self):
        """Process any pending votes"""
        # This would handle any votes stuck in pending state
        pass
        
    async def handle_consensus_request(self, event: Event):
        """Handle consensus requests"""
        if not self.running:
            return
            
        # Return current consensus status
        consensus_data = {
            'active_votes': len(self.active_votes),
            'vote_history': self.vote_history[-10:],
            'total_votes': len(self.vote_history),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="consensus_response",
            data=consensus_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_consensus_update(self):
        """Publish consensus data update"""
        consensus_data = {
            'active_votes': self.active_votes,
            'vote_history': self.vote_history[-5:],
            'total_votes': len(self.vote_history),
            'consensus_threshold': self.consensus_threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="consensus_update",
            data=consensus_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get consensus engine status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_votes': len(self.active_votes),
            'total_votes': len(self.vote_history),
            'consensus_threshold': self.consensus_threshold,
            'timestamp': datetime.now().isoformat()
        }
