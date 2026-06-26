"""
AlphaEdge Agent 13 – Sentiment Aggregator
Aggregates sentiment from free APIs
Weighted: F&G 40%, Reddit 30%, CryptoPanic 20%, CoinGecko 10%
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """
    Sentiment Aggregator – Aggregates sentiment from multiple free sources
    Stage 1: Free APIs only
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "sentiment_agg"
        self.running = False
        
        # Sentiment data
        self.source_scores = {}
        self.aggregated_score = 50
        self.history = []
        
        # Source weights
        self.weights = {
            'alternative_me': 0.40,
            'reddit': 0.30,
            'cryptopanic': 0.20,
            'coingecko': 0.10
        }
        
    async def start(self):
        """Start the sentiment aggregator"""
        logger.info("Sentiment Aggregator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("sentiment_source_update", self.handle_source_update)
        await self.event_bus.subscribe("sentiment_aggregation_request", self.handle_aggregation_request)
        
        # Start aggregation cycle
        asyncio.create_task(self.run_aggregation_cycle())
        
        logger.info("Sentiment Aggregator running")
        
    async def stop(self):
        """Stop the sentiment aggregator"""
        self.running = False
        logger.info("Sentiment Aggregator stopped")
        
    async def run_aggregation_cycle(self):
        """Run regular aggregation cycle"""
        while self.running:
            try:
                # Aggregate sentiment
                await self.aggregate_sentiment()
                
                # Calculate history trends
                await self.calculate_trends()
                
                # Publish aggregation update
                await self.publish_aggregation_update()
                
            except Exception as e:
                logger.error(f"Aggregation cycle error: {e}")
                
            await asyncio.sleep(180)  # Every 3 minutes
            
    async def handle_source_update(self, event: Event):
        """Handle sentiment source updates"""
        if not self.running:
            return
            
        source = event.data.get('source')
        score = event.data.get('score')
        
        if source and score is not None:
            self.source_scores[source] = score
            logger.debug(f"Updated {source}: {score}")
            
    async def aggregate_sentiment(self):
        """Aggregate sentiment from all sources"""
        if not self.source_scores:
            return
            
        weighted_sum = 0
        total_weight = 0
        
        for source, score in self.source_scores.items():
            weight = self.weights.get(source, 0)
            weighted_sum += score * weight
            total_weight += weight
            
        if total_weight > 0:
            self.aggregated_score = weighted_sum / total_weight
        else:
            self.aggregated_score = 50
            
        # Store in state
        await self.state_manager.set('aggregated_sentiment', self.aggregated_score)
        await self.state_manager.set('sentiment_sources', self.source_scores)
        
        # Add to history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'score': self.aggregated_score,
            'sources': self.source_scores.copy()
        })
        
        # Keep last 100 entries
        if len(self.history) > 100:
            self.history.pop(0)
            
        logger.info(f"Aggregated sentiment: {self.aggregated_score:.1f}/100")
        
    async def calculate_trends(self):
        """Calculate sentiment trends"""
        if len(self.history) < 10:
            return
            
        recent = [h['score'] for h in self.history[-10:]]
        older = [h['score'] for h in self.history[-20:-10]]
        
        # Calculate trend
        recent_avg = statistics.mean(recent) if recent else 50
        older_avg = statistics.mean(older) if older else 50
        
        trend = recent_avg - older_avg
        
        # Determine trend direction
        if trend > 5:
            direction = 'improving'
        elif trend < -5:
            direction = 'declining'
        else:
            direction = 'stable'
            
        # Store trend
        await self.state_manager.set('sentiment_trend', {
            'direction': direction,
            'magnitude': trend,
            'recent_avg': recent_avg,
            'older_avg': older_avg
        })
        
    async def publish_aggregation_update(self):
        """Publish sentiment aggregation update"""
        aggregation_data = {
            'aggregated_score': self.aggregated_score,
            'source_scores': self.source_scores,
            'history_length': len(self.history),
            'trend': await self.state_manager.get('sentiment_trend', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="sentiment_aggregation_update",
            data=aggregation_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_aggregation_request(self, event: Event):
        """Handle aggregation requests"""
        if not self.running:
            return
            
        aggregation_data = {
            'aggregated_score': self.aggregated_score,
            'source_scores': self.source_scores,
            'history_length': len(self.history),
            'trend': await self.state_manager.get('sentiment_trend', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="sentiment_aggregation_response",
            data=aggregation_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    def get_tps_contribution(self) -> float:
        """Get TPS contribution from sentiment (Stage 1: 3 points max)"""
        if self.aggregated_score >= 70:
            return 3.0
        elif self.aggregated_score >= 50:
            return 1.5
        else:
            return 0.0
            
    async def get_status(self) -> Dict[str, Any]:
        """Get sentiment aggregator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'aggregated_score': self.aggregated_score,
            'source_scores': self.source_scores,
            'history_length': len(self.history),
            'tps_contribution': self.get_tps_contribution(),
            'timestamp': datetime.now().isoformat()
        }
