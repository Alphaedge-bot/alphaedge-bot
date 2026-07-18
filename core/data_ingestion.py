# core/data_ingestion.py
# AlphaEdge V13.0.7 – Data Ingestion Pipeline
# Item 16 + Item 17: TimescaleDB Integration + Data Ingestion

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import asyncpg
from asyncpg import Pool

from core.rpc_manager import HedgedRPCManager

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Data Ingestion Pipeline for TimescaleDB
    Item 16 + Item 17: TimescaleDB Integration + Data Ingestion
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.pool: Optional[Pool] = None
        self.running = False
        self.buffer = []
        self.buffer_size = 100
        self.flush_interval = 10
        
        # Hedged RPC for data fetching
        self.rpc_manager = HedgedRPCManager(
            endpoints=[
                {"name": "Jito_SG", "url": "https://sg.jito.blockengine.me/api/v1/", "priority": 1},
                {"name": "Helius_SG", "url": "https://rpc.helius.xyz/?api-key=YOUR_API_KEY", "priority": 2}
            ]
        )
        
    async def connect(self):
        """Connect to TimescaleDB"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                min_size=2,
                max_size=self.config['pool_size'],
                max_inactive_connection_lifetime=self.config['pool_recycle']
            )
            logger.info("✅ TimescaleDB connected")
            return True
        except Exception as e:
            logger.error(f"TimescaleDB connection failed: {e}")
            return False
            
    async def start(self):
        """Start the ingestion pipeline"""
        if not await self.connect():
            return
            
        self.running = True
        logger.info("Data Ingestion Pipeline running")
        
        # Start flush loop
        asyncio.create_task(self._flush_loop())
        
        # Start data fetching loop
        asyncio.create_task(self._fetch_loop())
        
    async def stop(self):
        """Stop the ingestion pipeline"""
        self.running = False
        await self._flush()
        if self.pool:
            await self.pool.close()
        logger.info("Data Ingestion Pipeline stopped")
        
    async def _fetch_loop(self):
        """Fetch data from sources"""
        tokens = await self._get_tracked_tokens()
        
        while self.running:
            try:
                for token in tokens:
                    # Fetch OHLCV data
                    ohlcv = await self._fetch_ohlcv(token)
                    if ohlcv:
                        await self.ingest_ohlcv(ohlcv)
                        
                    # Fetch liquidity data
                    liquidity = await self._fetch_liquidity(token)
                    if liquidity:
                        await self.ingest_liquidity(liquidity)
                        
                await asyncio.sleep(60)  # Every minute
                
            except Exception as e:
                logger.error(f"Fetch loop error: {e}")
                await asyncio.sleep(5)
                
    async def _fetch_ohlcv(self, token: str) -> Dict:
        """Fetch OHLCV data from RPC"""
        # In production, fetch from blockchain/RPC
        # Simulating for now
        return {
            'time': datetime.now(),
            'token': token,
            'timeframe': '1m',
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 1000000,
            'source': 'rpc'
        }
        
    async def _fetch_liquidity(self, token: str) -> Dict:
        """Fetch liquidity data"""
        return {
            'time': datetime.now(),
            'token': token,
            'exchange': 'jupiter',
            'bid_depth': 500000,
            'ask_depth': 500000,
            'spread': 0.001,
            'best_bid': 99.95,
            'best_ask': 100.05
        }
        
    async def _get_tracked_tokens(self) -> List[str]:
        """Get list of tracked tokens"""
        return ['SOL', 'ETH', 'BTC']  # In production, fetch from state
        
    async def ingest_ohlcv(self, data: Dict):
        """Ingest OHLCV data into TimescaleDB"""
        query = """
        INSERT INTO ohlcv_data (
            time, token, timeframe, open, high, low, close, volume, source
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (time, token, timeframe) DO UPDATE
        SET open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
        
        self.buffer.append({
            'query': query,
            'params': (
                data['time'],
                data['token'],
                data['timeframe'],
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                data['source']
            )
        })
        
        if len(self.buffer) >= self.buffer_size:
            await self._flush()
            
    async def ingest_liquidity(self, data: Dict):
        """Ingest liquidity data"""
        query = """
        INSERT INTO liquidity_data (
            time, token, exchange, bid_depth, ask_depth, spread, best_bid, best_ask
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        self.buffer.append({
            'query': query,
            'params': (
                data['time'],
                data['token'],
                data['exchange'],
                data['bid_depth'],
                data['ask_depth'],
                data['spread'],
                data['best_bid'],
                data['best_ask']
            )
        })
        
        if len(self.buffer) >= self.buffer_size:
            await self._flush()
            
    async def _flush(self):
        """Flush buffer to database"""
        if not self.buffer or not self.pool:
            return
            
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for item in self.buffer:
                    await conn.execute(item['query'], *item['params'])
                    
        self.buffer = []
        logger.debug(f"Flushed {len(self.buffer)} records to TimescaleDB")
        
    async def _flush_loop(self):
        """Regular flush loop"""
        while self.running:
            await asyncio.sleep(self.flush_interval)
            if self.buffer:
                await self._flush()
                
    async def query_ohlcv(self, token: str, timeframe: str, 
                          start_time: datetime, end_time: datetime) -> List[Dict]:
        """Query OHLCV data from TimescaleDB"""
        query = """
        SELECT time, open, high, low, close, volume
        FROM ohlcv_data
        WHERE token = $1
        AND timeframe = $2
        AND time >= $3
        AND time <= $4
        ORDER BY time ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, token, timeframe, start_time, end_time)
            
        return [
            {
                'time': row['time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            }
            for row in rows
        ]
        
    async def query_aggregated(self, token: str, timeframe: str) -> Dict:
        """Query aggregated metrics"""
        query = """
        SELECT tps_score, zone_score, mcdx_score, smc_score, volume_24h, volatility
        FROM aggregated_metrics
        WHERE token = $1
        AND timeframe = $2
        ORDER BY time DESC
        LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, token, timeframe)
            
        if row:
            return {
                'tps_score': float(row['tps_score']) if row['tps_score'] else 0,
                'zone_score': float(row['zone_score']) if row['zone_score'] else 0,
                'mcdx_score': float(row['mcdx_score']) if row['mcdx_score'] else 0,
                'smc_score': float(row['smc_score']) if row['smc_score'] else 0,
                'volume_24h': float(row['volume_24h']) if row['volume_24h'] else 0,
                'volatility': float(row['volatility']) if row['volatility'] else 0
            }
        return {}
