"""
AlphaEdge Agent 07 – Sentiment Scanner
Free APIs only (Stage 1): Alternative.me, Reddit, CryptoPanic, CoinGecko
No Twitter data. No Grok daily. Twitter = Marketing only.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import random
import os

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SentimentScanner:
    """
    Sentiment Scanner – Free APIs only (Stage 1)
    Sources: Alternative.me (40%), Reddit (30%), CryptoPanic (20%), CoinGecko (10%)
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "sentiment"
        self.running = False
        
        # Sentiment cache
        self.sentiment_score = 50
        self.source_scores = {}
        self.history = []
        
        # API endpoints
        self.alternative_me_endpoint = "https://api.alternative.me/fng/"
        self.cryptopanic_endpoint = "https://cryptopanic.com/api/v1/posts/"
        self.coingecko_endpoint = "https://api.coingecko.com/api/v3/coins/"
        
        # API keys
        self.cryptopanic_key = os.getenv('CRYPTOPANIC_API_KEY', '')
        
        # Reddit subreddits
        self.subreddits = ['CryptoCurrency', 'Solana', 'ethereum']
        
    async def start(self):
        """Start the sentiment scanner"""
        logger.info("Sentiment Scanner starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("sentiment_request", self.handle_sentiment_request)
        
        # Start sentiment cycle
        asyncio.create_task(self.run_sentiment_cycle())
        
        logger.info("Sentiment Scanner running (Free APIs only)")
        
    async def stop(self):
        """Stop the sentiment scanner"""
        self.running = False
        logger.info("Sentiment Scanner stopped")
        
    async def run_sentiment_cycle(self):
        """Run regular sentiment scanning"""
        while self.running:
            try:
                # Get sentiment from all sources
                await self.scan_sentiment()
                
                # Calculate weighted score
                await self.calculate_sentiment_score()
                
                # Publish sentiment update
                await self.publish_sentiment_update()
                
            except Exception as e:
                logger.error(f"Sentiment cycle error: {e}")
                
            await asyncio.sleep(1800)  # Every 30 minutes (Stage 1)
            
    async def scan_sentiment(self):
        """Scan sentiment from all free sources"""
        # Alternative.me Fear & Greed (40% weight)
        alt_score = await self.get_alternative_me()
        
        # Reddit API (30% weight)
        reddit_score = await self.get_reddit_sentiment()
        
        # CryptoPanic (20% weight)
        panic_score = await self.get_cryptopanic()
        
        # CoinGecko Social (10% weight)
        gecko_score = await self.get_coingecko_social()
        
        self.source_scores = {
            'alternative_me': alt_score,
            'reddit': reddit_score,
            'cryptopanic': panic_score,
            'coingecko': gecko_score
        }
        
        logger.info(f"Sentiment scan complete: {self.source_scores}")
        
    async def get_alternative_me(self) -> float:
        """Get Fear & Greed Index from Alternative.me"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.alternative_me_endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('data', [{}])[0].get('value', 50))
        except Exception as e:
            logger.error(f"Alternative.me error: {e}")
        return 50
        
    async def get_reddit_sentiment(self) -> float:
        """Get sentiment from Reddit API"""
        sentiment_scores = []
        
        for subreddit in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={'User-Agent': 'AlphaEdge/1.0'}) as response:
                        if response.status == 200:
                            data = await response.json()
                            posts = data.get('data', {}).get('children', [])
                            
                            positive = 0
                            negative = 0
                            
                            for post in posts[:10]:
                                title = post.get('data', {}).get('title', '').lower()
                                upvote_ratio = post.get('data', {}).get('upvote_ratio', 0.5)
                                
                                # Simple sentiment based on upvote ratio
                                if upvote_ratio > 0.6:
                                    positive += 1
                                elif upvote_ratio < 0.4:
                                    negative += 1
                                    
                            total = positive + negative
                            if total > 0:
                                sentiment_scores.append((positive / total) * 100)
            except Exception as e:
                logger.error(f"Reddit error for {subreddit}: {e}")
                
        if sentiment_scores:
            return sum(sentiment_scores) / len(sentiment_scores)
        return 50
        
    async def get_cryptopanic(self) -> float:
        """Get sentiment from CryptoPanic"""
        if not self.cryptopanic_key:
            return 50
            
        try:
            params = {'auth_token': self.cryptopanic_key, 'limit': 30}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.cryptopanic_endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        positive = 0
                        negative = 0
                        
                        for news in data.get('results', [])[:20]:
                            sentiment = news.get('sentiment', 'neutral')
                            if sentiment == 'positive':
                                positive += 1
                            elif sentiment == 'negative':
                                negative += 1
                                
                        total = positive + negative
                        if total > 0:
                            return (positive / total) * 100
        except Exception as e:
            logger.error(f"CryptoPanic error: {e}")
        return 50
        
    async def get_coingecko_social(self) -> float:
        """Get social metrics from CoinGecko"""
        try:
            # Use SOL as default for testing
            url = f"{self.coingecko_endpoint}solana"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        social_data = data.get('community_data', {})
                        twitter_followers = social_data.get('twitter_followers', 0)
                        
                        if twitter_followers > 1000000:
                            return 80
                        elif twitter_followers > 500000:
                            return 70
                        elif twitter_followers > 100000:
                            return 60
                        elif twitter_followers > 50000:
                            return 50
        except Exception as e:
            logger.error(f"CoinGecko error: {e}")
        return 50
        
    async def calculate_sentiment_score(self):
        """Calculate weighted sentiment score (0-100)"""
        weights = {
            'alternative_me': 0.40,
            'reddit': 0.30,
            'cryptopanic': 0.20,
            'coingecko': 0.10
        }
        
        weighted_score = sum(
            self.source_scores.get(source, 50) * weight
            for source, weight in weights.items()
        )
        
        self.sentiment_score = round(weighted_score)
        
        # Store in state
        await self.state_manager.set('sentiment_score', self.sentiment_score)
        await self.state_manager.set('sentiment_sources', self.source_scores)
        
        logger.info(f"Sentiment score: {self.sentiment_score}/100")
        
    def get_tps_contribution(self) -> float:
        """Get TPS contribution from sentiment (Stage 1: 3 points max)"""
        if self.sentiment_score >= 70:
            return 3.0
        elif self.sentiment_score >= 50:
            return 1.5
        else:
            return 0.0
            
    async def publish_sentiment_update(self):
        """Publish sentiment data update"""
        sentiment_data = {
            'sentiment_score': self.sentiment_score,
            'source_scores': self.source_scores,
            'tps_contribution': self.get_tps_contribution(),
            'stage': 'Stage 1 (Free APIs)',
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="sentiment_data_update",
            data=sentiment_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_sentiment_request(self, event: Event):
        """Handle sentiment data requests"""
        if not self.running:
            return
            
        sentiment_data = {
            'sentiment_score': self.sentiment_score,
            'source_scores': self.source_scores,
            'tps_contribution': self.get_tps_contribution(),
            'stage': 'Stage 1 (Free APIs)',
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="sentiment_response",
            data=sentiment_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get sentiment scanner status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'sentiment_score': self.sentiment_score,
            'source_scores': self.source_scores,
            'stage': 'Stage 1 (Free APIs)',
            'update_frequency': '30 minutes',
            'tps_contribution': self.get_tps_contribution(),
            'timestamp': datetime.now().isoformat()
      }
