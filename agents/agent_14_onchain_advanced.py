"""
AlphaEdge Agent 14 – On-Chain Advanced
Advanced on-chain metrics (MVRV, NUPL, SOPR, etc.)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OnChainAdvanced:
    """On-Chain Advanced – Advanced on-chain metrics analysis"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "onchain_advanced"
        self.running = False
        
        # On-chain metrics cache
        self.metrics = {}
        self.anomalies = []
        self.history = []
        
        # Token list
        self.tokens = ['BTC', 'ETH', 'SOL', 'BNB', 'AVAX', 'MATIC', 'ARB']
        
    async def start(self):
        """Start the on-chain advanced agent"""
        logger.info("On-Chain Advanced starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("onchain_advanced_request", self.handle_onchain_advanced_request)
        
        # Start analysis cycle
        asyncio.create_task(self.run_onchain_cycle())
        
        logger.info("On-Chain Advanced running")
        
    async def stop(self):
        """Stop the on-chain advanced agent"""
        self.running = False
        logger.info("On-Chain Advanced stopped")
        
    async def run_onchain_cycle(self):
        """Run regular on-chain analysis"""
        while self.running:
            try:
                # Update all metrics
                for token in self.tokens:
                    await self.update_token_metrics(token)
                    
                # Detect anomalies
                await self.detect_anomalies()
                
                # Calculate overall score
                await self.calculate_overall_score()
                
                # Publish on-chain update
                await self.publish_onchain_update()
                
            except Exception as e:
                logger.error(f"On-chain cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def update_token_metrics(self, token: str):
        """Update metrics for a specific token"""
        # In production, fetch from blockchain APIs
        # For now, generate realistic sample data
        
        # MVRV (Market Value to Realized Value)
        mvrv = random.uniform(0.8, 2.5)
        
        # NUPL (Net Unrealized Profit/Loss)
        nupl = random.uniform(-0.3, 0.5)
        
        # SOPR (Spent Output Profit Ratio)
        sopr = random.uniform(0.9, 1.1)
        
        # Active addresses (24h)
        active_addresses = random.randint(10000, 1000000)
        
        # Exchange netflow (positive = inflow, negative = outflow)
        exchange_netflow = random.randint(-1000, 1000)
        
        # Whale count (>1M USD)
        whale_count = random.randint(10, 200)
        
        # Holder distribution
        holder_distribution = {
            'whales': random.uniform(0.1, 0.3),
            'institutions': random.uniform(0.2, 0.4),
            'retail': random.uniform(0.3, 0.6)
        }
        
        # Store metrics
        self.metrics[token] = {
            'mvrv': mvrv,
            'nupl': nupl,
            'sopr': sopr,
            'active_addresses': active_addresses,
            'exchange_netflow': exchange_netflow,
            'whale_count': whale_count,
            'holder_distribution': holder_distribution,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in state
        await self.state_manager.set(f'onchain_metrics_{token}', self.metrics[token])
        
    async def detect_anomalies(self):
        """Detect on-chain anomalies"""
        self.anomalies = []
        
        for token, metrics in self.metrics.items():
            # Check MVRV
            if metrics['mvrv'] > 2.0:
                self.anomalies.append({
                    'token': token,
                    'metric': 'mvrv',
                    'value': metrics['mvrv'],
                    'severity': 'high',
                    'description': f'MVRV {metrics["mvrv"]:.2f} indicates overvaluation'
                })
            elif metrics['mvrv'] < 0.8:
                self.anomalies.append({
                    'token': token,
                    'metric': 'mvrv',
                    'value': metrics['mvrv'],
                    'severity': 'medium',
                    'description': f'MVRV {metrics["mvrv"]:.2f} indicates undervaluation'
                })
                
            # Check NUPL
            if metrics['nupl'] > 0.3:
                self.anomalies.append({
                    'token': token,
                    'metric': 'nupl',
                    'value': metrics['nupl'],
                    'severity': 'medium',
                    'description': f'NUPL {metrics["nupl"]:.2f} indicates high profit-taking'
                })
            elif metrics['nupl'] < -0.2:
                self.anomalies.append({
                    'token': token,
                    'metric': 'nupl',
                    'value': metrics['nupl'],
                    'severity': 'high',
                    'description': f'NUPL {metrics["nupl"]:.2f} indicates capitulation'
                })
                
            # Check exchange netflow
            if metrics['exchange_netflow'] > 500:
                self.anomalies.append({
                    'token': token,
                    'metric': 'exchange_netflow',
                    'value': metrics['exchange_netflow'],
                    'severity': 'medium',
                    'description': f'Large inflow to exchanges: {metrics["exchange_netflow"]}'
                })
            elif metrics['exchange_netflow'] < -500:
                self.anomalies.append({
                    'token': token,
                    'metric': 'exchange_netflow',
                    'value': metrics['exchange_netflow'],
                    'severity': 'high',
                    'description': f'Large outflow from exchanges: {metrics["exchange_netflow"]}'
                })
                
        # Store anomalies
        await self.state_manager.set('onchain_anomalies', self.anomalies)
        
        if self.anomalies:
            logger.warning(f"Detected {len(self.anomalies)} on-chain anomalies")
            
    async def calculate_overall_score(self):
        """Calculate overall on-chain health score"""
        if not self.metrics:
            return
            
        scores = []
        
        for token, metrics in self.metrics.items():
            # Individual token score (0-100)
            score = 50  # Baseline
            
            # MVRV (ideal range: 0.8-1.5)
            if 0.8 <= metrics['mvrv'] <= 1.5:
                score += 10
            elif 1.5 < metrics['mvrv'] <= 2.0:
                score += 5
            else:
                score -= 10
                
            # NUPL (ideal: positive but not too high)
            if 0.05 <= metrics['nupl'] <= 0.3:
                score += 10
            elif metrics['nupl'] > 0.3:
                score += 5
            else:
                score -= 10
                
            # SOPR (ideal: >1.0)
            if metrics['sopr'] > 1.0:
                score += 5
            else:
                score -= 5
                
            # Exchange netflow (ideal: negative/outflow)
            if metrics['exchange_netflow'] < 0:
                score += 10
            else:
                score -= 5
                
            # Whale count (higher = more confidence)
            if metrics['whale_count'] > 100:
                score += 10
            elif metrics['whale_count'] > 50:
                score += 5
                
            scores.append({
                'token': token,
                'score': max(0, min(100, score)),
                'metrics': metrics
            })
            
        # Calculate average score
        avg_score = sum(s['score'] for s in scores) / len(scores) if scores else 50
        
        # Store scores
        await self.state_manager.set('onchain_scores', scores)
        await self.state_manager.set('onchain_avg_score', avg_score)
        
        logger.info(f"On-chain average score: {avg_score:.1f}/100")
        
    async def publish_onchain_update(self):
        """Publish on-chain data update"""
        onchain_data = {
            'metrics': self.metrics,
            'anomalies': self.anomalies,
            'scores': await self.state_manager.get('onchain_scores', []),
            'avg_score': await self.state_manager.get('onchain_avg_score', 50),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="onchain_advanced_update",
            data=onchain_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_onchain_advanced_request(self, event: Event):
        """Handle on-chain advanced data requests"""
        if not self.running:
            return
            
        onchain_data = {
            'metrics': self.metrics,
            'anomalies': self.anomalies,
            'scores': await self.state_manager.get('onchain_scores', []),
            'avg_score': await self.state_manager.get('onchain_avg_score', 50),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="onchain_advanced_response",
            data=onchain_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get on-chain advanced status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'tokens_monitored': len(self.metrics),
            'anomalies_detected': len(self.anomalies),
            'avg_score': await self.state_manager.get('onchain_avg_score', 50),
            'timestamp': datetime.now().isoformat()
        }
