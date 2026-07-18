"""
AlphaEdge Agent 63 – Profit Taking Executor
Execute orders (market/limit/TWAP/iceberg), minimize slippage, hide from MEV
V13.0.7 – UPDATED with Liquidity Filter + Sandwich Isolation Guard
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import json
import numpy as np

from core.event_bus import Event, EventBus
from core.state_manager import StateManager
from core.zone_detector import ZoneDetector

logger = logging.getLogger(__name__)


class ProfitTakingExecutor:
    """
    Profit Taking Executor – Executes profit-taking orders with minimal slippage
    V13.0.7 – Now with Liquidity Filter + Sandwich Isolation Guard
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "profit_taking_executor"
        self.running = False
        
        # Execution state
        self.pending_orders = []
        self.executed_orders = []
        self.execution_stats = {}
        
        self.config = {
            'default_order_type': 'limit',
            'max_slippage': 0.005,
            'twap_slices': 5,
            'iceberg_visible_pct': 0.10,
            'hide_from_mev': True
        }
        
        # ============================================
        # Gold Swap Configuration
        # ============================================
        self.gold_config = {
            'assets': {
                'paxg': {
                    'symbol': 'PAXG',
                    'name': 'Paxos Gold',
                    'priority': 1,
                    'chains': {
                        'solana': {'address': 'So111...', 'platforms': ['jupiter']},
                        'ethereum': {'address': '0x4580...', 'platforms': ['1inch', 'curve', 'uniswap']},
                        'bsc': {'address': '0x8ac7...', 'platforms': ['pancakeswap']}
                    },
                    'min_liquidity': 100000,
                    'max_deviation': 0.005,
                    'typical_spread': 0.002
                },
                'xaut': {
                    'symbol': 'XAUT',
                    'name': 'Tether Gold',
                    'priority': 2,
                    'chains': {
                        'ethereum': {'address': '0x6874...', 'platforms': ['1inch', 'uniswap']},
                        'bsc': {'address': '0x1b81...', 'platforms': ['pancakeswap']}
                    },
                    'min_liquidity': 50000,
                    'max_deviation': 0.01,
                    'typical_spread': 0.003
                }
            },
            'platforms': {
                'jupiter': {'enabled': True, 'chain': 'solana', 'fee': 0.002, 'priority': 1, 'mev_protection': True, 'supported_assets': ['paxg']},
                '1inch': {'enabled': True, 'chain': 'ethereum', 'fee': 0.001, 'priority': 2, 'mev_protection': True, 'supported_assets': ['paxg', 'xaut']},
                'curve': {'enabled': True, 'chain': 'ethereum', 'fee': 0.0004, 'priority': 3, 'mev_protection': True, 'supported_assets': ['paxg']},
                'pancakeswap': {'enabled': True, 'chain': 'bsc', 'fee': 0.0025, 'priority': 4, 'mev_protection': False, 'supported_assets': ['paxg', 'xaut']},
                'uniswap': {'enabled': True, 'chain': 'ethereum', 'fee': 0.003, 'priority': 5, 'mev_protection': False, 'supported_assets': ['paxg', 'xaut']}
            },
            'thresholds': {
                'min_usdt_amount': 100,
                'max_slippage': 0.015,
                'max_single_slippage': 0.005,
                'max_gas_fee': 5.0,
                'min_liquidity': 100000,
                'split_threshold': 5000,
                'max_orders': 5
            },
            'recovery': {
                'depeg_threshold': 0.01,
                'recovery_threshold': 0.005,
                'check_interval': 60,
                'max_retries': 3
            }
        }
        
        # Zone Detector
        self.zone_detector = ZoneDetector()
        self.zone_exit_data = {}
        
        # ============================================
        # ITEM 15: LIQUIDITY FILTER
        # ============================================
        self.liquidity_filter = {
            'enabled': True,
            'min_24h_volume': 500000,
            'min_order_book_depth': 50000,
            'max_spread': 0.005,
            'check_before_entry': True,
            'check_before_exit': False
        }
        
        # ============================================
        # ITEM 36: SANDWICH ISOLATION GUARD
        # ============================================
        self.sandwich_guard = {
            'enabled': True,
            'strict_ledger_checks': True,
            'verify_min_output': True,
            'slippage_buffer': 0.02,
            'fail_atomically': True,
            'check_pool_depth': True
        }
        
    async def start(self):
        """Start the profit taking executor"""
        logger.info("Profit Taking Executor starting...")
        self.running = True
        
        await self.event_bus.subscribe("profit_take_request", self.handle_profit_take_request)
        await self.event_bus.subscribe("order_status_request", self.handle_order_status_request)
        await self.event_bus.subscribe("execution_cancel_request", self.handle_execution_cancel)
        await self.event_bus.subscribe("depeg_detected", self.handle_depeg)
        await self.event_bus.subscribe("stablecoin_recovered", self.handle_recovery)
        await self.event_bus.subscribe("gold_swap_requested", self.handle_swap_request)
        await self.event_bus.subscribe("stable_recovery_requested", self.handle_stable_recovery_request)
        await self.event_bus.subscribe("zone_tp_hit", self.handle_zone_tp_hit)
        await self.event_bus.subscribe("zone_sl_hit", self.handle_zone_sl_hit)
        await self.event_bus.subscribe("price_update", self.handle_price_update)
        
        asyncio.create_task(self.run_execution_cycle())
        logger.info("Profit Taking Executor running")
        
    async def stop(self):
        """Stop the profit taking executor"""
        self.running = False
        logger.info("Profit Taking Executor stopped")
        
    async def run_execution_cycle(self):
        """Run regular execution cycle"""
        while self.running:
            try:
                await self.process_pending_orders()
                await self.update_order_status()
                await self.check_zone_exits()
                await self.publish_execution_update()
            except Exception as e:
                logger.error(f"Execution cycle error: {e}")
            await asyncio.sleep(1)
            
    # ============================================
    # ITEM 15: LIQUIDITY FILTER
    # ============================================
    
    async def check_liquidity(self, token: str, trade_type: str = 'entry') -> Dict:
        """Check liquidity conditions before execution"""
        result = {'approved': True, 'reason': ''}
        
        if not self.liquidity_filter['enabled']:
            return result
        
        if trade_type == 'entry' and not self.liquidity_filter['check_before_entry']:
            return result
        
        if trade_type == 'exit' and not self.liquidity_filter['check_before_exit']:
            return result
        
        try:
            volume_24h = await self._get_24h_volume(token)
            if volume_24h < self.liquidity_filter['min_24h_volume']:
                result['approved'] = False
                result['reason'] = f'24h volume ${volume_24h:,.0f} below ${self.liquidity_filter["min_24h_volume"]:,.0f}'
                return result
            
            depth = await self._get_order_book_depth(token)
            if depth < self.liquidity_filter['min_order_book_depth']:
                result['approved'] = False
                result['reason'] = f'Order book depth ${depth:,.0f} below ${self.liquidity_filter["min_order_book_depth"]:,.0f}'
                return result
            
            spread = await self._get_current_spread(token)
            if spread > self.liquidity_filter['max_spread']:
                result['approved'] = False
                result['reason'] = f'Spread {spread*100:.2f}% above {self.liquidity_filter["max_spread"]*100:.2f}%'
                return result
                
        except Exception as e:
            logger.error(f"Liquidity check error: {e}")
            result['approved'] = False
            result['reason'] = str(e)
            
        return result
    
    async def _get_24h_volume(self, token: str) -> float:
        return 1000000  # Simulated
    
    async def _get_order_book_depth(self, token: str) -> float:
        return 500000  # Simulated
    
    async def _get_current_spread(self, token: str) -> float:
        return 0.001  # 0.1%
    
    # ============================================
    # ITEM 36: SANDWICH ISOLATION GUARD
    # ============================================
    
    async def execute_sandwich_isolated_swap(self, token: str, amount: float, slippage: float) -> Dict:
        """Execute swap with Sandwich Isolation Guard"""
        result = {'status': 'failed', 'reason': ''}
        
        if not self.sandwich_guard['enabled']:
            return await self._execute_swap(token, amount, slippage)
        
        try:
            pool_state = await self._get_pool_state(token)
            expected_output = await self._calculate_expected_output(token, amount, pool_state)
            min_output = expected_output * (1 - slippage - self.sandwich_guard['slippage_buffer'])
            
            if self.sandwich_guard['strict_ledger_checks']:
                ledger_verified = await self._verify_ledger_accounts(token, pool_state)
                if not ledger_verified:
                    result['reason'] = 'Ledger verification failed'
                    return result
            
            if self.sandwich_guard['check_pool_depth']:
                pool_depth = await self._get_pool_depth(token)
                if amount > pool_depth * 0.05:
                    result['reason'] = f'Amount ${amount:,.0f} exceeds 5% of pool depth ${pool_depth:,.0f}'
                    return result
            
            if self.sandwich_guard['fail_atomically']:
                swap_result = await self._execute_swap_with_min_output(token, amount, min_output)
                if swap_result['status'] != 'success':
                    result['reason'] = f'Swap failed: {swap_result.get("reason", "Unknown")}'
                    return result
                    
                if self.sandwich_guard['verify_min_output']:
                    actual_output = swap_result.get('output_amount', 0)
                    if actual_output < min_output:
                        result['reason'] = f'Actual output ${actual_output:,.2f} below minimum ${min_output:,.2f}'
                        return result
                        
                result = {'status': 'success', 'output': actual_output}
            else:
                result = await self._execute_swap(token, amount, slippage)
                
        except Exception as e:
            logger.error(f"Sandwich isolation error: {e}")
            result['reason'] = str(e)
            
        return result
    
    async def _get_pool_state(self, token: str) -> Dict:
        return {'reserve_0': 1000000, 'reserve_1': 1000000, 'total_supply': 2000000, 'price': 100.0, 'liquidity': 2000000}
    
    async def _calculate_expected_output(self, token: str, amount: float, pool_state: Dict) -> float:
        return amount * 0.99
    
    async def _verify_ledger_accounts(self, token: str, pool_state: Dict) -> bool:
        return True
    
    async def _get_pool_depth(self, token: str) -> float:
        return 2000000
    
    async def _execute_swap_with_min_output(self, token: str, amount: float, min_output: float) -> Dict:
        return {'status': 'success', 'output_amount': amount * 0.98, 'tx_hash': f'0x{hash(str(datetime.now()))[:64]}'}
    
    async def _execute_swap(self, token: str, amount: float, slippage: float) -> Dict:
        return {'status': 'success', 'output_amount': amount * 0.98, 'tx_hash': f'0x{hash(str(datetime.now()))[:64]}'
