"""
AlphaEdge Agent 04 – Whale On-Chain Analyst
Whale transactions, exchange netflow, MVRV, NUPL, SOPR, per block
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class WhaleOnChainAnalyst:
    """Whale On-Chain Analyst – Monitors on-chain metrics and whale activity"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "whale"
        self.running = False
        
        # On-chain metrics cache
        self.whale_transactions = []
        self.exchange_netflow = {}
        self.mvrv = {}
        self.nupl = {}
        self.sopr = {}
        
        # Whale thresholds
        self.whale_threshold = 1000000  # $1M in USD
        
    async def start(self):
        """Start the whale analyst"""
        logger.info("Whale On-Chain Analyst starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("onchain_request", self.handle_onchain_request)
        
        # Start monitoring cycle
        asyncio.create_task(self.run_onchain_cycle())
        
        logger.info("Whale On-Chain Analyst running")
        
    async def stop(self):
        """Stop the whale analyst"""
        self.running = False
        logger.info("Whale On-Chain Analyst stopped")
        
    async def run_onchain_cycle(self):
        """Run regular on-chain monitoring"""
        while self.running:
            try:
                # Update whale transactions
                await self.update_whale_transactions()
                
                # Update exchange netflow
                await self.update_exchange_netflow()
                
                # Update MVRV
                await self.update_mvrv()
                
                # Update NUPL
                await self.update_nupl()
                
                # Update SOPR
                await self.update_sopr()
                
                # Publish on-chain update
                await self.publish_onchain_update()
                
            except Exception as e:
                logger.error(f"On-chain cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def update_whale_transactions(self):
        """Update whale transaction data"""
        # In production, fetch from blockchain APIs
        # For now, generate sample data
        sample_transactions = [
            {
                'hash': f'0x{random.randint(100000, 999999):06d}',
                'from': f'0x{random.randint(100000, 999999):06d}',
                'to': f'0x{random.randint(100000, 999999):06d}',
                'value': random.randint(1000000, 10000000),
                'token': 'USDC',
                'timestamp': datetime.now().isoformat()
            }
            for _ in range(random.randint(1, 5))
        ]
        
        self.whale_transactions = sample_transactions
        
        # Store in state
        await self.state_manager.set('whale_transactions', sample_transactions)
        
        logger.info(f"Updated {len(sample_transactions)} whale transactions")
        
    async def update_exchange_netflow(self):
        """Update exchange netflow data"""
        # In production, fetch from blockchain APIs
        # For now, generate sample data
        exchanges = ['Binance', 'Coinbase', 'Kraken', 'Bybit', 'OKX']
        
        for exchange in exchanges:
            netflow = random.randint(-500, 500)  # Positive = inflow, Negative = outflow
            self.exchange_netflow[exchange] = netflow
            
        # Store in state
        await self.state_manager.set('exchange_netflow', self.exchange_netflow)
        
        logger.info(f"Updated exchange netflow for {len(exchanges)} exchanges")
        
    async def update_mvrv(self):
        """Update MVRV (Market Value to Realized Value) ratio"""
        # In production, fetch from blockchain APIs
        # For now, generate sample data
        tokens = ['BTC', 'ETH', 'SOL', 'BNB', 'AVAX']
        
        for token in tokens:
            # MVRV > 1 = overvalued, < 1 = undervalued
            self.mvrv[token] = random.uniform(0.8, 2.5)
            
        # Store in state
        await self.state_manager.set('mvrv', self.mvrv)
        
        logger.info("Updated MVRV data")
        
    async def update_nupl(self):
        """Update NUPL (Net Unrealized Profit/Loss)"""
        # In production, fetch from blockchain APIs
        # For now, generate sample data
        tokens = ['BTC', 'ETH', 'SOL', 'BNB', 'AVAX']
        
        for token in tokens:
            # NUPL > 0 = profit, < 0 = loss
            self.nupl[token] = random.uniform(-0.3, 0.5)
            
        # Store in state
        await self.state_manager.set('nupl', self.nupl)
        
        logger.info("Updated NUPL data")
        
    async def update_sopr(self):
        """Update SOPR (Spent Output Profit Ratio)"""
        # In production, fetch from blockchain APIs
        # For now, generate sample data
        tokens = ['BTC', 'ETH', 'SOL', 'BNB', 'AVAX']
        
        for token in tokens:
            # SOPR > 1 = profit, < 1 = loss
            self.sopr[token] = random.uniform(0.9, 1.1)
            
        # Store in state
        await self.state_manager.set('sopr', self.sopr)
        
        logger.info("Updated SOPR data")
        
    def calculate_whale_score(self) -> float:
        """Calculate whale activity score (0-100)"""
        score = 50  # Baseline
        
        # Check whale transactions
        whale_count = len(self.whale_transactions)
        if whale_count > 10:
            score += 20
        elif whale_count > 5:
            score += 10
            
        # Check exchange netflow
        netflow_sum = sum(self.exchange_netflow.values())
        if netflow_sum < 0:  # Net outflow = bullish
            score += 20
        elif netflow_sum > 0:  # Net inflow = bearish
            score -= 20
            
        # Check MVRV
        avg_mvrv = sum(self.mvrv.values()) / len(self.mvrv) if self.mvrv else 1.5
        if avg_mvrv < 1.2:
            score += 10
        elif avg_mvrv > 2.0:
            score -= 10
            
        return min(100, max(0, score))
        
    async def publish_onchain_update(self):
        """Publish on-chain data update"""
        whale_score = self.calculate_whale_score()
        
        onchain_data = {
            'whale_transactions': self.whale_transactions,
            'exchange_netflow': self.exchange_netflow,
            'mvrv': self.mvrv,
            'nupl': self.nupl,
            'sopr': self.sopr,
            'whale_score': whale_score,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="onchain_data_update",
            data=onchain_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_onchain_request(self, event: Event):
        """Handle on-chain data requests"""
        if not self.running:
            return
            
        onchain_data = {
            'whale_transactions': self.whale_transactions,
            'exchange_netflow': self.exchange_netflow,
            'mvrv': self.mvrv,
            'nupl': self.nupl,
            'sopr': self.sopr,
            'whale_score': self.calculate_whale_score(),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="onchain_response",
            data=onchain_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get whale analyst status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'whale_transactions': len(self.whale_transactions),
            'exchange_netflow': self.exchange_netflow,
            'mvrv': self.mvrv,
            'nupl': self.nupl,
            'sopr': self.sopr,
            'whale_score': self.calculate_whale_score(),
            'timestamp': datetime.now().isoformat()
  }
