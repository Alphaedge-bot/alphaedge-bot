"""
AlphaEdge Agent 03 – Macro Analyst
Market regime detection, Fed Net Liquidity, Global Liquidity, DXY, Real Yields
TA/PA for Fed Liquidity
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MacroAnalyst:
    """Macro Analyst – Monitors global macro conditions"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "macro"
        self.running = False
        
        # Macro data cache
        self.fed_liquidity = {
            'score': 50,
            'trend': 'neutral',
            'components': {}
        }
        self.dxy = {
            'price': 0.0,
            'trend': 'neutral'
        }
        self.gold = {
            'price': 0.0,
            'trend': 'neutral'
        }
        self.real_yields = 0.0
        
        # FRED API endpoints
        self.fred_endpoints = {
            'walcl': 'https://api.stlouisfed.org/fred/series/observations',
            'wtreg': 'https://api.stlouisfed.org/fred/series/observations',
            'rrp': 'https://api.stlouisfed.org/fred/series/observations'
        }
        
    async def start(self):
        """Start the macro analyst"""
        logger.info("Macro Analyst starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("macro_request", self.handle_macro_request)
        
        # Start macro monitoring cycle
        asyncio.create_task(self.run_macro_cycle())
        
        logger.info("Macro Analyst running")
        
    async def stop(self):
        """Stop the macro analyst"""
        self.running = False
        logger.info("Macro Analyst stopped")
        
    async def run_macro_cycle(self):
        """Run regular macro monitoring"""
        while self.running:
            try:
                # Update Fed liquidity
                await self.update_fed_liquidity()
                
                # Update DXY
                await self.update_dxy()
                
                # Update Gold
                await self.update_gold()
                
                # Update real yields
                await self.update_real_yields()
                
                # Calculate macro score
                await self.calculate_macro_score()
                
                # Publish macro update
                await self.publish_macro_update()
                
            except Exception as e:
                logger.error(f"Macro cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def update_fed_liquidity(self):
        """Update Fed Net Liquidity data"""
        try:
            # Calculate Fed Net Liquidity = WALCL - WTREGEN - RRPONTTLD
            walcl = await self._fetch_fred_series('WALCL')
            wtreg = await self._fetch_fred_series('WTREGEN')
            rrp = await self._fetch_fred_series('RRPONTTLD')
            
            fed_liquidity = walcl - wtreg - rrp
            
            # Calculate score (0-100)
            # This is a simplified scoring model
            # In production, use historical data for percentiles
            self.fed_liquidity['score'] = self._calculate_liquidity_score(fed_liquidity)
            self.fed_liquidity['trend'] = self._calculate_trend(self.fed_liquidity['score'])
            self.fed_liquidity['components'] = {
                'walcl': walcl,
                'wtreg': wtreg,
                'rrp': rrp,
                'net_liquidity': fed_liquidity
            }
            
            logger.info(f"Fed Liquidity updated: {fed_liquidity:.2f} (score: {self.fed_liquidity['score']})")
            
        except Exception as e:
            logger.error(f"Fed Liquidity update failed: {e}")
            
    async def _fetch_fred_series(self, series_id: str) -> float:
        """Fetch a series from FRED API"""
        # In production, use actual FRED API
        # For now, return sample data
        sample_data = {
            'WALCL': 1500000,
            'WTREGEN': 500000,
            'RRPONTTLD': 200000
        }
        return sample_data.get(series_id, 0)
        
    def _calculate_liquidity_score(self, liquidity: float) -> float:
        """Calculate liquidity score (0-100)"""
        # This is a simplified scoring model
        # In production, use historical percentiles
        base_score = 50
        
        # Adjust based on trend
        if liquidity > 1000000:
            return 80
        elif liquidity > 800000:
            return 60
        elif liquidity > 500000:
            return 40
        else:
            return 20
            
    def _calculate_trend(self, score: float) -> str:
        """Calculate trend direction"""
        if score >= 80:
            return 'strong_expansion'
        elif score >= 60:
            return 'expansion'
        elif score >= 40:
            return 'neutral'
        elif score >= 20:
            return 'contraction'
        else:
            return 'strong_contraction'
            
    async def update_dxy(self):
        """Update DXY (US Dollar Index)"""
        try:
            # In production, fetch from API
            # For now, use sample data
            self.dxy['price'] = 104.5  # Sample
            self.dxy['trend'] = 'neutral'  # rising, falling, neutral
            
            logger.info(f"DXY updated: {self.dxy['price']}")
            
        except Exception as e:
            logger.error(f"DXY update failed: {e}")
            
    async def update_gold(self):
        """Update Gold price"""
        try:
            # In production, fetch from API
            # For now, use sample data
            self.gold['price'] = 3960  # Sample (below $4K)
            self.gold['trend'] = 'falling'
            
            logger.info(f"Gold updated: {self.gold['price']}")
            
        except Exception as e:
            logger.error(f"Gold update failed: {e}")
            
    async def update_real_yields(self):
        """Update real yields"""
        try:
            # In production, fetch from API
            # For now, use sample data
            self.real_yields = 2.5  # Sample
            
            logger.info(f"Real yields updated: {self.real_yields}%")
            
        except Exception as e:
            logger.error(f"Real yields update failed: {e}")
            
    async def calculate_macro_score(self):
        """Calculate overall macro score"""
        # Weighted combination of macro factors
        score = 0.0
        
        # Fed liquidity (40%)
        score += self.fed_liquidity['score'] * 0.40
        
        # DXY (30%) - lower DXY = higher score
        dxy_score = 50
        if self.dxy['trend'] == 'falling':
            dxy_score = 70
        elif self.dxy['trend'] == 'rising':
            dxy_score = 30
        score += dxy_score * 0.30
        
        # Real yields (30%) - lower yields = higher score
        yield_score = 50
        if self.real_yields < 1.0:
            yield_score = 70
        elif self.real_yields > 3.0:
            yield_score = 30
        score += yield_score * 0.30
        
        # Store macro score
        await self.state_manager.set('macro_score', score)
        await self.state_manager.set('fed_liquidity_score', self.fed_liquidity['score'])
        await self.state_manager.set('dxy_trend', self.dxy['trend'])
        
        logger.info(f"Macro score: {score:.1f}")
        
    async def publish_macro_update(self):
        """Publish macro data update"""
        macro_data = {
            'fed_liquidity': self.fed_liquidity,
            'dxy': self.dxy,
            'gold': self.gold,
            'real_yields': self.real_yields,
            'macro_score': await self.state_manager.get('macro_score', 50),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="macro_data_update",
            data=macro_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def handle_macro_request(self, event: Event):
        """Handle macro data requests"""
        if not self.running:
            return
            
        macro_data = {
            'fed_liquidity': self.fed_liquidity,
            'dxy': self.dxy,
            'gold': self.gold,
            'real_yields': self.real_yields,
            'macro_score': await self.state_manager.get('macro_score', 50),
            'timestamp': datetime.now().isoformat()
        }
        
        response = Event(
            event_type="macro_response",
            data=macro_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get macro analyst status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'fed_liquidity_score': self.fed_liquidity['score'],
            'fed_liquidity_trend': self.fed_liquidity['trend'],
            'dxy_price': self.dxy['price'],
            'dxy_trend': self.dxy['trend'],
            'gold_price': self.gold['price'],
            'real_yields': self.real_yields,
            'macro_score': await self.state_manager.get('macro_score', 50),
            'timestamp': datetime.now().isoformat()
  }
