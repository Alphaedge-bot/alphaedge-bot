"""
AlphaEdge Agent 08 – Oracle Latency Tracker
Multi-oracle price validation: Pyth (50%), Chainlink (30%), CoinGecko (20%)
Deviation threshold 1%, stale price threshold 5 seconds
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import statistics

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class OracleLatencyTracker:
    """
    Oracle Latency Tracker – Multi-oracle price validation
    Primary: Pyth (50%), Secondary: Chainlink (30%), Tertiary: CoinGecko (20%)
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "oracle"
        self.running = False
        
        # Price cache
        self.price_data = {}
        self.latency_data = {}
        self.deviation_data = {}
        
        # Oracle endpoints
        self.pyth_endpoint = "https://pyth.network/api"
        self.chainlink_endpoint = "https://data.chain.link/api"
        self.coingecko_endpoint = "https://api.coingecko.com/api/v3/coins"
        
        # Token mapping
        self.token_map = {
            'SOL': 'solana',
            'ETH': 'ethereum',
            'BTC': 'bitcoin',
            'BNB': 'bnb',
            'AVAX': 'avalanche-2'
        }
        
        # Weights
        self.weights = {
            'pyth': 0.50,
            'chainlink': 0.30,
            'coingecko': 0.20
        }
        
        # Thresholds
        self.deviation_threshold = 1.0  # 1%
        self.stale_threshold = 5.0  # 5 seconds
        
    async def start(self):
        """Start the oracle tracker"""
        logger.info("Oracle Latency Tracker starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("oracle_request", self.handle_oracle_request)
        
        # Start oracle cycle
        asyncio.create_task(self.run_oracle_cycle())
        
        logger.info("Oracle Latency Tracker running")
        
    async def stop(self):
        """Stop the oracle tracker"""
        self.running = False
        logger.info("Oracle Latency Tracker stopped")
        
    async def run_oracle_cycle(self):
        """Run regular oracle monitoring"""
        while self.running:
            try:
                # Update prices from all oracles
                await self.update_all_prices()
                
                # Calculate weighted median
                await self.calculate_validated_price()
                
                # Check deviations
                await self.check_deviations()
                
                # Check staleness
                await self.check_staleness()
                
                # Publish oracle update
                await self.publish_oracle_update()
                
            except Exception as e:
                logger.error(f"Oracle cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def update_all_prices(self):
        """Update prices from all oracles"""
        tokens = ['SOL', 'ETH', 'BTC', 'BNB', 'AVAX']
        
        for token in tokens:
            self.price_data[token] = {}
            
            # Pyth
            pyth_price = await self.get_pyth_price(token)
            if pyth_price:
                self.price_data[token]['pyth'] = pyth_price
                
            # Chainlink
            chainlink_price = await self.get_chainlink_price(token)
            if chainlink_price:
                self.price_data[token]['chainlink'] = chainlink_price
                
            # CoinGecko
            coingecko_price = await self.get_coingecko_price(token)
            if coingecko_price:
                self.price_data[token]['coingecko'] = coingecko_price
                
    async def get_pyth_price(self, token: str) -> Optional[float]:
        """Get price from Pyth Oracle"""
        try:
            start_time = time.time()
            
            # Simulate API call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Sample price data
            sample_prices = {
                'SOL': 160.0,
                'ETH': 3500.0,
                'BTC': 61000.0,
                'BNB': 600.0,
                'AVAX': 40.0
            }
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            self.latency_data['pyth'] = latency
            
            return sample_prices.get(token, 0)
            
        except Exception as e:
            logger.error(f"Pyth error for {token}: {e}")
            return None
            
    async def get_chainlink_price(self, token: str) -> Optional[float]:
        """Get price from Chainlink Oracle"""
        try:
            start_time = time.time()
            
            # Simulate API call
            await asyncio.sleep(0.2)  # Simulate network delay
            
            # Sample price data (slightly different for deviation testing)
            sample_prices = {
                'SOL': 161.0,  # 0.6% higher
                'ETH': 3490.0,  # 0.3% lower
                'BTC': 61050.0,
                'BNB': 598.0,
                'AVAX': 40.5
            }
            
            latency = (time.time() - start_time) * 1000
            self.latency_data['chainlink'] = latency
            
            return sample_prices.get(token, 0)
            
        except Exception as e:
            logger.error(f"Chainlink error for {token}: {e}")
            return None
            
    async def get_coingecko_price(self, token: str) -> Optional[float]:
        """Get price from CoinGecko"""
        try:
            start_time = time.time()
            
            # Simulate API call
            await asyncio.sleep(0.3)  # Simulate network delay
            
            # Sample price data (more deviation for testing)
            sample_prices = {
                'SOL': 159.5,  # 0.9% lower
                'ETH': 3520.0,  # 0.6% higher
                'BTC': 60800.0,
                'BNB': 602.0,
                'AVAX': 39.8
            }
            
            latency = (time.time() - start_time) * 1000
            self.latency_data['coingecko'] = latency
            
            return sample_prices.get(token, 0)
            
        except Exception as e:
            logger.error(f"CoinGecko error for {token}: {e}")
            return None
            
    async def calculate_validated_price(self):
        """Calculate weighted median price from all oracles"""
        for token, prices in self.price_data.items():
            if len(prices) < 2:
                continue
                
            # Get all available prices
            price_list = list(prices.values())
            
            # Calculate median
            median_price = statistics.median(price_list)
            
            # Calculate weighted average
            weighted_sum = 0
            total_weight = 0
            
            for source, price in prices.items():
                weight = self.weights.get(source, 0)
                weighted_sum += price * weight
                total_weight += weight
                
            if total_weight > 0:
                weighted_price = weighted_sum / total_weight
            else:
                weighted_price = median_price
                
            # Store validated price
            self.price_data[token]['validated_price'] = weighted_price
            self.price_data[token]['median_price'] = median_price
            
            # Store in state
            await self.state_manager.set(f'price_{token}', weighted_price)
            await self.state_manager.set(f'price_median_{token}', median_price)
            
            logger.info(f"{token} validated price: {weighted_price:.2f}")
            
    async def check_deviations(self):
        """Check for oracle deviations"""
        for token, prices in self.price_data.items():
            if 'validated_price' not in prices:
                continue
                
            validated = prices['validated_price']
            deviations = {}
            
            for source, price in prices.items():
                if source == 'validated_price' or source == 'median_price':
                    continue
                    
                deviation = abs(price - validated) / validated * 100
                deviations[source] = deviation
                
                if deviation > self.deviation_threshold:
                    logger.warning(f"{token} {source} deviation: {deviation:.2f}%")
                    
            self.deviation_data[token] = deviations
            
    async def check_staleness(self):
        """Check for stale oracle data"""
        # In production, check timestamp of last update
        # For now, use latency as proxy
        for token, prices in self.price_data.items():
            stale_sources = []
            
            for source in prices.keys():
                if source not in ['validated_price', 'median_price']:
                    latency = self.latency_data.get(source, 0)
                    if latency > self.stale_threshold * 1000:  # Convert to ms
                        stale_sources.append(source)
                        
            if stale_sources:
                logger.warning(f"{token} stale data from: {stale_sources}")
                
    async def publish_oracle_update(self):
        """Publish oracle data update"""
        oracle_data = {
            'prices': self.price_data,
            'latency': self.latency_data,
            'deviations': self.deviation_data,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="oracle_data_update",
            data=oracle_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_oracle_request(self, event: Event):
        """Handle oracle data requests"""
        if not self.running:
            return
            
        oracle_data = {
            'prices': self.price_data,
            'latency': self.latency_data,
            'deviations': self.deviation_data,
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="oracle_response",
            data=oracle_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get oracle tracker status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'oracles_active': len(self.price_data),
            'average_latency': sum(self.latency_data.values()) / len(self.latency_data) if self.latency_data else 0,
            'oracles': list(self.price_data.keys()),
            'timestamp': datetime.now().isoformat()
          }
