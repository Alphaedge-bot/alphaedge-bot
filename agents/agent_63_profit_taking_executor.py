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
        return {'status': 'success', 'output_amount': amount * 0.98, 'tx_hash': f'0x{hash(str(datetime.now()))[:64]}'}

    async def check_zone_exits(self):
        """Check zone-based exits"""
        positions = await self.state_manager.get('positions', {})
        for token, position in positions.items():
            if token in self.zone_exit_data:
                current_price = position.get('price', 0)
                zone_data = self.zone_exit_data[token]
                
                tp = zone_data.get('tp')
                if tp and current_price >= tp:
                    await self.execute_zone_exit(token, 'take_profit', current_price)
                
                sl = zone_data.get('sl')
                if sl and current_price <= sl:
                    await self.execute_zone_exit(token, 'stop_loss', current_price)

    async def execute_zone_exit(self, token: str, reason: str, price: float):
        """Execute zone-based exit"""
        logger.info(f"🔄 Zone-based exit for {token}: {reason} at {price}")
        
        positions = await self.state_manager.get('positions', {})
        position = positions.get(token, {})
        
        order = {
            'token': token,
            'side': 'sell',
            'price': price,
            'quantity': position.get('quantity', 0),
            'type': 'market'
        }
        
        result = await self._execute_swap(token, order.get('quantity', 0), 0.01)
        
        await self.event_bus.publish(Event(
            event_type="position_exit",
            data={
                'token': token,
                'reason': reason,
                'price': price,
                'order_result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        ))

    async def handle_zone_tp_hit(self, event: Event):
        if not self.running:
            return
        token = event.data.get('token')
        price = event.data.get('price', 0)
        if token:
            await self.execute_zone_exit(token, 'zone_take_profit', price)

    async def handle_zone_sl_hit(self, event: Event):
        if not self.running:
            return
        token = event.data.get('token')
        price = event.data.get('price', 0)
        if token:
            await self.execute_zone_exit(token, 'zone_stop_loss', price)

    async def handle_price_update(self, event: Event):
        if not self.running:
            return
        token = event.data.get('token')
        price = event.data.get('price', 0)
        price_data = event.data.get('price_data', [])
        if token and price_data:
            await self.update_zone_data(token, price, price_data)

    async def update_zone_data(self, token: str, current_price: float, price_data: List[Dict]):
        try:
            if len(price_data) < 50:
                return
            
            highs = [p.get('high', 0) for p in price_data]
            lows = [p.get('low', 0) for p in price_data]
            closes = [p.get('close', 0) for p in price_data]
            volumes = [p.get('volume', 0) for p in price_data]
            opens = [p.get('open', 0) for p in price_data]
            
            high_arr = np.array(highs)
            low_arr = np.array(lows)
            close_arr = np.array(closes)
            vol_arr = np.array(volumes)
            open_arr = np.array(opens)
            
            zones = self.zone_detector.detect_zones(
                high_arr, low_arr, close_arr, vol_arr, open_arr
            )
            
            nearest_demand = self.zone_detector.get_nearest_zone(current_price, -1)
            nearest_supply = self.zone_detector.get_nearest_zone(current_price, 1)
            
            self.zone_exit_data[token] = {
                'sl': nearest_demand.bottom * 0.998 if nearest_demand else None,
                'tp': nearest_supply.top if nearest_supply else None,
                'sl_zone_score': nearest_demand.score if nearest_demand else 0,
                'tp_zone_score': nearest_supply.score if nearest_supply else 0,
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Zone data update error: {e}")

    async def process_pending_orders(self):
        """Process pending orders"""
        pass

    async def update_order_status(self):
        """Update order status"""
        pass

    async def get_current_price(self, token: str) -> float:
        prices = {'SOL': 160.0, 'ETH': 3500.0, 'BTC': 61000.0, 'BNB': 600.0, 'AVAX': 40.0, 'PAXG': 3960.0, 'XAUT': 3965.0, 'GOLD': 3960.0}
        return prices.get(token, 100.0)

    async def publish_execution_update(self):
        gold_holdings = await self.state_manager.get('gold_holdings', {})
        execution_data = {
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'recent_executions': self.executed_orders[-5:],
            'execution_stats': self.execution_stats,
            'gold_holdings': gold_holdings,
            'zone_exits_active': len(self.zone_exit_data),
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="profit_taking_execution_update", data=execution_data, source=self.agent_id)
        await self.event_bus.publish(event)

    async def handle_profit_take_request(self, event: Event):
        if not self.running:
            return
        request_id = event.data.get('request_id')
        order = event.data.get('order')
        order_type = order.get('type', self.config['default_order_type'])
        
        if order_type == 'limit':
            result = await self.execute_limit_order(order)
        elif order_type == 'twap':
            result = await self.execute_twap_order(order)
        elif order_type == 'iceberg':
            result = await self.execute_iceberg_order(order)
        else:
            result = await self.execute_market_order(order)
            
        response = Event(
            event_type="profit_take_response",
            data={'request_id': request_id, 'order': order, 'result': result, 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)

    async def handle_order_status_request(self, event: Event):
        if not self.running:
            return
        order_id = event.data.get('order_id')
        order = None
        for o in self.pending_orders:
            if o.get('id') == order_id:
                order = o
                break
        if not order:
            for o in self.executed_orders:
                if o.get('id') == order_id:
                    order = o
                    break
        response = Event(
            event_type="order_status_response",
            data={'order_id': order_id, 'order': order, 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)

    async def handle_execution_cancel(self, event: Event):
        if not self.running:
            return
        order_id = event.data.get('order_id')
        order = None
        for i, o in enumerate(self.pending_orders):
            if o.get('id') == order_id:
                order = self.pending_orders.pop(i)
                break
        if order:
            order['status'] = 'cancelled'
            self.executed_orders.append(order)
            logger.info(f"Order cancelled: {order_id}")
        response = Event(
            event_type="execution_cancel_response",
            data={'order_id': order_id, 'cancelled': bool(order), 'timestamp': datetime.now().isoformat()},
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)

    async def execute_limit_order(self, order: Dict) -> Dict:
        order_id = f"limit_{datetime.now().timestamp()}"
        result = {'id': order_id, 'type': 'limit', 'token': order.get('token'), 'side': order.get('side', 'sell'), 'price': order.get('price', 0), 'quantity': order.get('quantity', 0), 'status': 'pending', 'timestamp': datetime.now().isoformat()}
        self.pending_orders.append(result)
        return {'status': 'queued', 'order_id': order_id, 'estimated_execution_time': 'immediate'}

    async def execute_twap_order(self, order: Dict) -> Dict:
        order_id = f"twap_{datetime.now().timestamp()}"
        quantity = order.get('quantity', 0)
        slices = self.config['twap_slices']
        slice_quantity = quantity / slices
        result = {'id': order_id, 'type': 'twap', 'token': order.get('token'), 'side': order.get('side', 'sell'), 'quantity': quantity, 'slices': slices, 'slice_quantity': slice_quantity, 'status': 'pending', 'timestamp': datetime.now().isoformat()}
        self.pending_orders.append(result)
        return {'status': 'queued', 'order_id': order_id, 'estimated_execution_time': f'{slices} slices'}

    async def execute_iceberg_order(self, order: Dict) -> Dict:
        order_id = f"iceberg_{datetime.now().timestamp()}"
        quantity = order.get('quantity', 0)
        visible_pct = self.config['iceberg_visible_pct']
        visible_quantity = quantity * visible_pct
        result = {'id': order_id, 'type': 'iceberg', 'token': order.get('token'), 'side': order.get('side', 'sell'), 'quantity': quantity, 'visible_quantity': visible_quantity, 'status': 'pending', 'timestamp': datetime.now().isoformat()}
        self.pending_orders.append(result)
        return {'status': 'queued', 'order_id': order_id, 'estimated_execution_time': 'multiple_slices'}

    async def execute_market_order(self, order: Dict) -> Dict:
        order_id = f"market_{datetime.now().timestamp()}"
        result = {'id': order_id, 'type': 'market', 'token': order.get('token'), 'side': order.get('side', 'sell'), 'quantity': order.get('quantity', 0), 'status': 'pending', 'timestamp': datetime.now().isoformat()}
        self.pending_orders.append(result)
        return {'status': 'queued', 'order_id': order_id, 'estimated_execution_time': 'immediate'}

    async def handle_depeg(self, event: Event):
        logger.info(f"⚠️ Depeg detected! Event data: {event.data}")
        holdings = await self.state_manager.get('wallet_1_holdings', {})
        usdt_amount = holdings.get('USDT', 0)
        usdc_amount = holdings.get('USDC', 0)
        total_stable = usdt_amount + usdc_amount
        if total_stable > self.gold_config['thresholds']['min_usdt_amount']:
            await self.execute_gold_swap(total_stable, preferred_asset='paxg')
        else:
            logger.info(f"Stable holdings ${total_stable} below minimum")

    async def handle_recovery(self, event: Event):
        logger.info(f"✅ Stablecoins recovered! Event data: {event.data}")
        await self.execute_stable_swap()

    async def handle_swap_request(self, event: Event):
        amount = event.data.get('amount', 0)
        asset = event.data.get('asset', 'paxg')
        if amount > 0:
            await self.execute_gold_swap(amount, preferred_asset=asset)
        else:
            logger.warning("Invalid swap request amount")

    async def handle_stable_recovery_request(self, event: Event):
        asset = event.data.get('asset', None)
        amount = event.data.get('amount', None)
        await self.execute_stable_swap(asset=asset, amount=amount)

    async def execute_gold_swap(self, usdt_amount: float, preferred_asset: str = 'paxg', preferred_chain: str = None) -> Dict:
        logger.info(f"🚀 Executing USDT → {preferred_asset.upper()} swap for ${usdt_amount}")
        min_amount = self.gold_config['thresholds']['min_usdt_amount']
        if usdt_amount < min_amount:
            return {'status': 'failed', 'reason': f'Amount ${usdt_amount} below minimum ${min_amount}'}
        
        asset_available = await self.check_asset_availability(preferred_asset, usdt_amount)
        if not asset_available and preferred_asset == 'paxg':
            logger.warning("⚠️ PAXG unavailable, trying XAUT as fallback")
            preferred_asset = 'xaut'
            asset_available = await self.check_asset_availability(preferred_asset, usdt_amount)
        if not asset_available:
            return {'status': 'failed', 'reason': f'Both PAXG and XAUT unavailable'}
        
        platform = await self.find_best_platform_for_asset(usdt_amount, preferred_asset)
        if not platform:
            return {'status': 'failed', 'reason': f'No suitable platform found for {preferred_asset}'}
        
        split_threshold = self.gold_config['thresholds']['split_threshold']
        if usdt_amount > split_threshold:
            return await self.execute_split_swap(usdt_amount, platform, preferred_asset)
        else:
            return await self.execute_single_swap(usdt_amount, platform, preferred_asset)

    async def check_asset_availability(self, asset: str, amount: float) -> bool:
        asset_config = self.gold_config['assets'].get(asset)
        if not asset_config:
            return False
        total_liquidity = 0
        for chain, chain_config in asset_config['chains'].items():
            liquidity = await self.get_asset_liquidity(asset.upper(), chain)
            total_liquidity += liquidity
        current_price = await self.get_current_price(asset.upper())
        gold_price = await self.get_current_price('GOLD')
        deviation = abs(current_price - gold_price) / gold_price if gold_price > 0 else 1
        return (total_liquidity >= asset_config['min_liquidity'] and deviation <= asset_config['max_deviation'])

    async def get_asset_liquidity(self, asset: str, chain: str) -> float:
        liquidity = {'PAXG': {'solana': 5000000, 'ethereum': 2000000, 'bsc': 500000}, 'XAUT': {'ethereum': 1000000, 'bsc': 300000}}
        return liquidity.get(asset, {}).get(chain, 0)

    async def find_best_platform_for_asset(self, usdt_amount: float, asset: str) -> Optional[Dict]:
        asset_config = self.gold_config['assets'].get(asset)
        if not asset_config:
            return None
        supported_platforms = []
        for chain, chain_config in asset_config['chains'].items():
            supported_platforms.extend(chain_config['platforms'])
        candidates = []
        for name in supported_platforms:
            platform = self.gold_config['platforms'].get(name)
            if not platform or not platform.get('enabled', True):
                continue
            metrics = await self.get_platform_metrics_for_asset(name, platform, usdt_amount, asset)
            if metrics:
                candidates.append({'name': name, 'chain': platform['chain'], 'asset': asset, 'metrics': metrics, 'total_cost': metrics['fees'] + metrics['slippage'] + metrics['gas_cost'], 'score': self.calculate_platform_score(metrics, usdt_amount)})
        if not candidates:
            return None
        candidates.sort(key=lambda x: (x['total_cost'], -x['score']))
        return candidates[0]

    async def get_platform_metrics_for_asset(self, name: str, platform: Dict, amount: float, asset: str) -> Optional[Dict]:
        try:
            if platform['chain'] == 'solana':
                gas_cost = 0.01
                mev_protection = True
            elif platform['chain'] == 'bsc':
                gas_cost = 0.10
                mev_protection = False
            else:
                gas_cost = 5.00
                mev_protection = True
            if asset == 'paxg':
                fee_rate = platform.get('fee', 0.002)
                slippage_rate = 0.001 if platform['chain'] == 'solana' else 0.0015
                liquidity = await self.get_asset_liquidity('PAXG', platform['chain'])
            else:
                fee_rate = platform.get('fee', 0.003)
                slippage_rate = 0.0025
                liquidity = await self.get_asset_liquidity('XAUT', platform['chain'])
            fees = fee_rate * amount
            slippage = slippage_rate * amount
            if amount > liquidity * 0.1 and liquidity > 0:
                slippage *= (1 + (amount / liquidity))
            return {'fees': fees, 'slippage': slippage, 'gas_cost': gas_cost, 'liquidity': liquidity, 'execution_time': 0.5 if platform['chain'] == 'solana' else 1.0, 'mev_protection': mev_protection}
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return None

    def calculate_platform_score(self, metrics: Dict, amount: float) -> float:
        score = 0
        fee_rate = metrics.get('fees', 0) / amount if amount > 0 else 0
        score += 30 * (1 - min(fee_rate / 0.01, 1))
        slippage_rate = metrics.get('slippage', 0) / amount if amount > 0 else 0
        score += 25 * (1 - min(slippage_rate / 0.01, 1))
        liquidity = metrics.get('liquidity', 0)
        score += 20 * min(liquidity / 1000000, 1)
        gas_cost = metrics.get('gas_cost', 10)
        score += 15 * (1 - min(gas_cost / 10, 1))
        if metrics.get('mev_protection', False):
            score += 10
        return score

    async def execute_single_swap(self, usdt_amount: float, platform: Dict, asset: str) -> Dict:
        try:
            quote = await self.get_quote(usdt_amount, platform, asset)
            if not quote:
                return {'status': 'failed', 'reason': 'Quote unavailable'}
            max_slippage = self.gold_config['thresholds']['max_single_slippage']
            if quote.get('slippage', 0) > max_slippage:
                return {'status': 'failed', 'reason': f"Slippage {quote['slippage']*100:.2f}% > {max_slippage*100:.2f}%"}
            asset_price = await self.get_current_price(asset.upper())
            asset_received = (usdt_amount / asset_price) * (1 - quote['slippage'])
            result = {'status': 'executed', 'platform': platform['name'], 'chain': platform['chain'], 'asset': asset.upper(), 'usdt_amount': usdt_amount, 'asset_received': asset_received, 'asset_price': asset_price, 'fees': quote['fees'], 'slippage': quote['slippage'], 'gas_cost': quote['gas_cost'], 'total_cost': quote['total_cost'], 'tx_hash': f"0x{hash(str(datetime.now()))[:64]}", 'timestamp': datetime.now().isoformat()}
            await self.store_gold_swap(result, asset)
            await self.event_bus.publish(Event(event_type="gold_swap_executed", data=result, source=self.agent_id))
            logger.info(f"✅ Swap executed: ${usdt_amount} → {asset_received:.4f} {asset.upper()}")
            return result
        except Exception as e:
            logger.error(f"Swap execution failed: {e}")
            return {'status': 'failed', 'reason': str(e)}

    async def execute_split_swap(self, usdt_amount: float, platform: Dict, asset: str) -> Dict:
        max_orders = self.gold_config['thresholds']['max_orders']
        num_orders = min(max_orders, int(usdt_amount / self.gold_config['thresholds']['split_threshold']) + 1)
        order_size = usdt_amount / num_orders
        logger.info(f"📊 Splitting ${usdt_amount} into {num_orders} orders of ${order_size:.2f}")
        results = []
        total_asset = 0
        for i in range(num_orders):
            result = await self.execute_single_swap(order_size, platform, asset)
            if result['status'] == 'executed':
                total_asset += result.get('asset_received', 0)
                results.append(result)
            else:
                logger.warning(f"Order {i+1} failed: {result.get('reason', 'Unknown')}")
        return {'status': 'executed', 'platform': platform['name'], 'chain': platform['chain'], 'asset': asset.upper(), 'total_usdt': usdt_amount, 'total_asset': total_asset, 'avg_price': usdt_amount / total_asset if total_asset > 0 else 0, 'num_orders': len(results), 'successful_orders': len([r for r in results if r['status'] == 'executed']), 'failed_orders': len([r for r in results if r['status'] == 'failed']), 'orders': results, 'timestamp': datetime.now().isoformat()}

    async def get_quote(self, usdt_amount: float, platform: Dict, asset: str) -> Optional[Dict]:
        try:
            asset_price = await self.get_current_price(asset.upper())
            expected_asset = usdt_amount / asset_price if asset_price > 0 else 0
            metrics = platform.get('metrics', {})
            fees = metrics.get('fees', 0)
            slippage = metrics.get('slippage', 0) / usdt_amount if usdt_amount > 0 else 0
            gas_cost = metrics.get('gas_cost', 0)
            return {'asset_price': asset_price, 'expected_asset': expected_asset, 'fees': fees, 'slippage': slippage, 'gas_cost': gas_cost, 'total_cost': fees + slippage * usdt_amount + gas_cost, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None

    async def execute_stable_swap(self, asset: str = None, amount: float = None) -> Dict:
        holdings = await self.state_manager.get('gold_holdings', {})
        if asset:
            assets_to_swap = {asset: holdings.get(asset, 0)}
        else:
            assets_to_swap = {'paxg': holdings.get('paxg', 0), 'xaut': holdings.get('xaut', 0)}
        assets_to_swap = {k: v for k, v in assets_to_swap.items() if v > 0}
        if not assets_to_swap:
            return {'status': 'failed', 'reason': 'No gold holdings to swap'}
        results = []
        total_usdt = 0
        for asset_name, asset_amount in assets_to_swap.items():
            if amount and asset_name != asset:
                continue
            logger.info(f"🔄 Swapping {asset_amount} {asset_name.upper()} → USDT")
            usdt_value = asset_amount * await self.get_current_price(asset_name.upper())
            platform = await self.find_best_platform_for_asset(usdt_value, asset_name)
            if not platform:
                logger.warning(f"No platform for {asset_name}")
                continue
            asset_price = await self.get_current_price(asset_name.upper())
            usdt_received = asset_amount * asset_price * (1 - 0.002)
            result = {'status': 'executed', 'platform': platform['name'], 'chain': platform['chain'], 'asset': asset_name.upper(), 'asset_amount': asset_amount, 'usdt_received': usdt_received, 'timestamp': datetime.now().isoformat()}
            results.append(result)
            total_usdt += usdt_received
            holdings[asset_name] = 0
        await self.state_manager.set('gold_holdings', holdings)
        await self.event_bus.publish(Event(event_type="stable_recovery_executed", data={'total_usdt': total_usdt, 'results': results, 'timestamp': datetime.now().isoformat()}, source=self.agent_id))
        logger.info(f"✅ Recovery complete: ${total_usdt:.2f} USDT")
        return {'status': 'executed', 'total_usdt': total_usdt, 'results': results, 'timestamp': datetime.now().isoformat()}

    async def store_gold_swap(self, result: Dict, asset: str):
        holdings = await self.state_manager.get('gold_holdings', {})
        holdings[asset] = holdings.get(asset, 0) + result.get('asset_received', 0)
        holdings['last_swap'] = result
        holdings['last_update'] = datetime.now().isoformat()
        await self.state_manager.set('gold_holdings', holdings)
        history = await self.state_manager.get('gold_swap_history', [])
        history.append(result)
        if len(history) > 100:
            history = history[-100:]
        await self.state_manager.set('gold_swap_history', history)

    async def get_status(self) -> Dict[str, Any]:
        gold_holdings = await self.state_manager.get('gold_holdings', {})
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'execution_stats': self.execution_stats,
            'config': self.config,
            'gold_holdings': gold_holdings,
            'gold_swap_count': len(await self.state_manager.get('gold_swap_history', [])),
            'liquidity_filter_enabled': self.liquidity_filter['enabled'],
            'sandwich_guard_enabled': self.sandwich_guard['enabled'],
            'timestamp': datetime.now().isoformat()
        }
