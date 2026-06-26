"""
AlphaEdge Agent 17 – Opponent (Bearish)
Argues AGAINST entry using Ticker Performance Score (TPS)
Finds flaws/risks in TPS components
3 debate rounds with Proposer
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class Opponent:
    """Opponent – Argues AGAINST entry with risk analysis and counter-evidence"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "opponent"
        self.running = False
        
        # Debate state
        self.active_debates = {}
        self.opposition_history = []
        
    async def start(self):
        """Start the opponent agent"""
        logger.info("Opponent starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("debate_start", self.handle_debate_start)
        await self.event_bus.subscribe("debate_rebuttal", self.handle_debate_rebuttal)
        
        logger.info("Opponent running")
        
    async def stop(self):
        """Stop the opponent agent"""
        self.running = False
        logger.info("Opponent stopped")
        
    async def handle_debate_start(self, event: Event):
        """Handle debate start from Proposer"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        proposal = event.data.get('proposal')
        round_num = event.data.get('round')
        
        logger.info(f"Debate started for {proposal_id} (Round {round_num})")
        
        # Analyze proposal for weaknesses
        weaknesses = await self.analyze_weaknesses(proposal)
        
        # Prepare opposition arguments
        opposition = {
            'proposal_id': proposal_id,
            'round': round_num,
            'arguments': weaknesses,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store opposition
        self.opposition_history.append(opposition)
        self.active_debates[proposal_id] = opposition
        
        # Send opposition arguments
        response_event = Event(
            event_type="debate_response",
            data=opposition,
            source=self.agent_id
        )
        await self.event_bus.publish(response_event)
        
        logger.info(f"Opposition sent for {proposal_id}")
        
    async def analyze_weaknesses(self, proposal: Dict) -> Dict:
        """Analyze proposal for weaknesses and risks"""
        evidence = proposal.get('evidence', {})
        tps = evidence.get('tps', 0)
        
        weaknesses = {
            'points': [],
            'risk_factors': [],
            'overall_risk': 'medium'
        }
        
        # Check TPS components
        technical = evidence.get('technical', {})
        onchain = evidence.get('onchain', {})
        macro = evidence.get('macro', 50)
        sentiment = evidence.get('sentiment', 50)
        
        # Technical weaknesses
        rsi = technical.get('rsi', 50)
        if rsi > 70:
            weaknesses['points'].append(f"RSI {rsi} indicates overbought conditions")
        elif rsi < 30:
            weaknesses['points'].append(f"RSI {rsi} indicates weak momentum")
            
        macd = technical.get('macd', {})
        if macd.get('macd', 0) < 0:
            weaknesses['points'].append("MACD bearish crossover detected")
            
        # On-chain weaknesses
        mvrv = onchain.get('mvrv', 0)
        if mvrv > 2.0:
            weaknesses['points'].append(f"MVRV {mvrv:.2f} indicates overvaluation")
        elif mvrv < 0.8:
            weaknesses['points'].append(f"MVRV {mvrv:.2f} indicates weak fundamentals")
            
        exchange_netflow = onchain.get('exchange_netflow', 0)
        if exchange_netflow > 0:
            weaknesses['points'].append("Positive exchange netflow (selling pressure)")
            
        # Macro weaknesses
        if macro < 40:
            weaknesses['points'].append(f"Poor macro conditions (score: {macro})")
            
        # Sentiment weaknesses
        if sentiment < 40:
            weaknesses['points'].append(f"Negative sentiment (score: {sentiment})")
            
        # Risk factors
        if tps < 82:
            weaknesses['risk_factors'].append(f"TPS {tps} below entry threshold")
            
        if rsi > 75:
            weaknesses['risk_factors'].append("High RSI (overextended)")
            
        if exchange_netflow > 500:
            weaknesses['risk_factors'].append("Large exchange inflow (potential dumping)")
            
        # Overall risk assessment
        if len(weaknesses['risk_factors']) >= 3:
            weaknesses['overall_risk'] = 'high'
        elif len(weaknesses['risk_factors']) >= 1:
            weaknesses['overall_risk'] = 'medium'
        else:
            weaknesses['overall_risk'] = 'low'
            
        return weaknesses
        
    async def handle_debate_rebuttal(self, event: Event):
        """Handle rebuttal from Proposer"""
        if not self.running:
            return
            
        proposal_id = event.data.get('proposal_id')
        round_num = event.data.get('round')
        rebuttal = event.data.get('rebuttal')
        
        logger.info(f"Rebuttal received for {proposal_id} (Round {round_num})")
        
        # Counter the rebuttal
        counter = await self.counter_rebuttal(proposal_id, rebuttal, round_num)
        
        # If not final round, send counter-arguments
        if round_num < 3:
            counter_event = Event(
                event_type="debate_response",
                data={
                    'proposal_id': proposal_id,
                    'round': round_num + 1,
                    'arguments': counter,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(counter_event)
        else:
            # Final round - determine winner
            winner = await self.determine_winner(proposal_id)
            
            # End debate
            end_event = Event(
                event_type="debate_round_end",
                data={
                    'proposal_id': proposal_id,
                    'round': round_num,
                    'result': winner,
                    'timestamp': datetime.now().isoformat()
                },
                source=self.agent_id
            )
            await self.event_bus.publish(end_event)
            
    async def counter_rebuttal(self, proposal_id: str, rebuttal: Dict, 
                               round_num: int) -> Dict:
        """Counter the Proposer's rebuttal"""
        # Get original opposition
        opposition = self.active_debates.get(proposal_id)
        
        if not opposition:
            return {'points': ['No arguments found']}
            
        # Prepare counter-arguments
        counter_points = []
        
        # Rebut each strength claimed by Proposer
        for strength in rebuttal.get('strengths', []):
            if 'TPS' in strength:
                # Oppose TPS claim
                counter_points.append(
                    "TPS alone doesn't guarantee entry success"
                )
            elif 'macro' in strength:
                # Oppose macro claim
                counter_points.append(
                    "Macro conditions can change rapidly"
                )
            elif 'technical' in strength:
                # Oppose technical claim
                counter_points.append(
                    "Technical indicators can be misleading in volatile markets"
                )
                
        return {
            'points': counter_points,
            'counter_to': rebuttal,
            'round': round_num
        }
        
    async def determine_winner(self, proposal_id: str) -> Dict:
        """Determine debate winner based on arguments"""
        # Get proposal and opposition
        proposal = None
        opposition = self.active_debates.get(proposal_id)
        
        for p in self.opposition_history:
            if p.get('proposal_id') == proposal_id:
                # This is the Proposer's final position
                pass
                
        # Simple winner determination
        # Count arguments from both sides
        if opposition:
            risk_factors = len(opposition.get('arguments', {}).get('risk_factors', []))
            
            if risk_factors >= 3:
                winner = 'opponent'
                confidence = 0.7
            elif risk_factors >= 1:
                winner = 'opponent'
                confidence = 0.5
            else:
                winner = 'proposer'
                confidence = 0.6
        else:
            winner = 'proposer'
            confidence = 0.5
            
        return {
            'winner': winner,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_status(self) -> Dict[str, Any]:
        """Get opponent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_debates': len(self.active_debates),
            'oppositions_made': len(self.opposition_history),
            'timestamp': datetime.now().isoformat()
        }
