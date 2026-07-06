"""
AlphaEdge Agent 63 – Profit Taking Executor
Execute orders (market/limit/TWAP/iceberg), minimize slippage, hide from MEV
V13.0.5 – UPDATED with PAXG + XAUT Support (Option B)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import json

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingExecutor:
    """
    Profit Taking Executor – Executes profit-taking orders with minimal slippage
    V13.0.5 – Now with PAXG + XAUT Gold Swap Strategy
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
        
        # Configuration
        self.config = {
            'default_order_type': 'limit',
            'max_slippage': 0.005,  # 0.5%
            'twap_slices': 5,
            'iceberg_visible_pct': 0.10,  # 10% visible
            'hide_from_mev': True
        }
        
        # ============================================
        # GOLD SWAP CONFIGURATION (PAXG + XAUT)
        # ============================================
        self.gold_config = {
            'assets': {
                'paxg': {
                    'symbol': 'PAXG',
                    'name': 'Paxos Gold',
                    'priority': 1,  # Primary
                    'chains': {
                        'solana': {
                            'address': 'So11111111111111111111111111111111111111112',
                            'platforms': ['jupiter']
                        },
                        'ethereum': {
                            'address': '0x45804880De29f0709cF3988aB34E7fcc72A57880',
                            'platforms': ['1inch', 'curve', 'uniswap']
                        },
                        'bsc': {
                            'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
                            'platforms': ['pancakeswap']
                        }
                    },
                    'min_liquidity': 100000,  # $100K minimum
                    'max_deviation': 0.005,   # 0.5% from gold price
                    'typical_spread': 0.002   # 0.2%
                },
                'xaut': {
                    'symbol': 'XAUT',
                    'name': 'Tether Gold',
                    'priority': 2,  # Fallback
                    'chains': {
                        'ethereum': {
                            'address': '0x68749665FF8D2d112Fa859AA293F07A622782F38',
                            'platforms': ['1inch', 'uniswap']
                        },
                        'bsc': {
                            'address': '0x1b81D678ffb9C0263b24A97847620C99d213eB14',
                            'platforms': ['pancakeswap']
                        }
                    },
                    'min_liquidity': 50000,   # $50K minimum
                    'max_deviation': 0.01,    # 1.0% from gold price
                    'typical_spread': 0.003   # 0.3%
                }
            },
            'platforms': {
                'jupiter': {
                    'enabled': True,
                    'chain': 'solana',
                    'fee': 0.002,
                    'priority': 1,
                    'mev_protection': True,
                    'supported_assets': ['paxg']
                },
                '1inch': {
                    'enabled': True,
                    'chain': 'ethereum',
                    'fee': 0.001,
                    'priority': 2,
                    'mev_protection': True,
                    'supported_assets': ['paxg', 'xaut']
                },
                'curve': {
                    'enabled': True,
                    'chain': 'ethereum',
                    'fee': 0.0004,
                    'priority': 3,
                    'mev_protection': True,
                    'supported_assets': ['paxg']
                },
                'pancakeswap': {
                    'enabled': True,
                    'chain': 'bsc',
                    'fee': 0.0025,
                    'priority': 4,
                    'mev_protection': False,
                    'supported_assets': ['paxg', 'xaut']
                },
                'uniswap': {
                    'enabled': True,
                    'chain': 'ethereum',
                    'fee': 0.003,
                    'priority': 5,
                    'mev_protection': False,
                    'supported_assets': ['paxg', 'xaut']
                }
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
        
    async def start(self):
        """Start the profit taking executor"""
        logger.info("Profit Taking Executor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("profit_take_request", self.handle_profit_take_request)
        await self.event_bus.subscribe("order_status_request", self.handle_order_status_request)
        await self.event_bus.subscribe("execution_cancel_request", self.handle_execution_cancel)
        
        # Gold swap event subscriptions
        await self.event_bus.subscribe("depeg_detected", self.handle_depeg)
        await self.event_bus.subscribe("stablecoin_recovered", self.handle_recovery)
        await self.event_bus.subscribe("gold_swap_requested", self.handle_swap_request)
        await self.event_bus.subscribe("stable_recovery_requested", self.handle_stable_recovery_request)
        
        # Start execution cycle
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
                # Process pending orders
                await self.process_pending_orders()
                
                # Update order status
                await self.update_order_status()
                
                # Publish execution update
                await self.publish_execution_update()
                
            except Exception as e:
                logger.error(f"Execution cycle error: {e}")
                
            await asyncio.sleep(1)  # Every second
            
    # ============================================
    # EXISTING ORDER HANDLERS (PRESERVED)
    # ============================================
    
    async def handle_profit_take_request(self, event: Event):
        """Handle profit taking requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        order = event.data.get('order')
        order_type = order.get('type', self.config['default_order_type'])
        
        logger.info(f"Profit take request: {request_id} ({order_type})")
        
        # Route to appropriate execution method
        if order_type == 'limit':
            result = await self.execute_limit_order(order)
        elif order_type == 'twap':
            result = await self.execute_twap_order(order)
        elif order_type == 'iceberg':
            result = await self.execute_iceberg_order(order)
        else:
            result = await self.execute_market_order(order)
            
        # Send response
        response = Event(
            event_type="profit_take_response",
            data={
                'request_id': request_id,
                'order': order,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_order_status_request(self, event: Event):
        """Handle order status requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        
        # Find order
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
            data={
                'order_id': order_id,
                'order': order,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_execution_cancel(self, event: Event):
        """Handle execution cancellation requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        order = None
        
        # Find and remove from pending
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
            data={
                'order_id': order_id,
                'cancelled': bool(order),
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    # ============================================
    # EXISTING ORDER EXECUTION METHODS (PRESERVED)
    # ============================================
    
    async def execute_limit_order(self, order: Dict) -> Dict:
        """Execute a limit order"""
        order_id = f"limit_{datetime.now().timestamp()}"
        
        result = {
            'id': order_id,
            'type': 'limit',
            'token': order.get('token'),
            'side': order.get('side', 'sell'),
            'price': order.get('price', 0),
            'quantity': order.get('quantity', 0),
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        self.pending_orders.append(result)
        
        return {
            'status': 'queued',
            'order_id': order_id,
            'estimated_execution_time': 'immediate'
        }
        
    async def execute_twap_order(self, order: Dict) -> Dict:
        """Execute a TWAP order"""
        order_id = f"twap_{datetime.now().timestamp()}"
        quantity = order.get('quantity', 0)
        slices = self.config['twap_slices']
        slice_quantity = quantity / slices
        
        result = {
            'id': order_id,
            'type': 'twap',
            'token': order.get('token'),
            'side': order.get('side', 'sell'),
            'quantity': quantity,
            'slices': slices,
            'slice_quantity': slice_quantity,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        self.pending_orders.append(result)
        
        return {
            'status': 'queued',
            'order_id': order_id,
            'estimated_execution_time': f'{slices} slices'
        }
        
    async def execute_iceberg_order(self, order: Dict) -> Dict:
        """Execute an iceberg order"""
        order_id = f"iceberg_{datetime.now().timestamp()}"
        quantity = order.get('quantity', 0)
        visible_pct = self.config['iceberg_visible_pct']
        visible_quantity = quantity * visible_pct
        
        result = {
            'id': order_id,
            'type': 'iceberg',
            'token': order.get('token'),
            'side': order.get('side', 'sell'),
            'quantity': quantity,
            'visible_quantity': visible_quantity,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        self.pending_orders.append(result)
        
        return {
            'status': 'queued',
            'order_id': order_id,
            'estimated_execution_time': 'multiple_slices'
        }
        
    async def execute_market_order(self, order: Dict) -> Dict:
        """Execute a market order"""
        order_id = f"market_{datetime.now().timestamp()}"
        
        result = {
            'id': order_id,
            'type': 'market',
            'token': order.get('token'),
            'side': order.get('side', 'sell'),
            'quantity': order.get('quantity', 0),
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        self.pending_orders.append(result)
        
        return {
            'status': 'queued',
            'order_id': order_id,
            'estimated_execution_time': 'immediate'
        }
        
    async def process_pending_orders(self):
        """Process pending orders"""
        for order in self.pending_orders[:10]:  # Process up to 10
            if order['status'] != 'pending':
                continue
                
            # Simulate execution
            await asyncio.sleep(0.1)
            
            # Check if order should be executed
            if order['type'] == 'limit':
                # Execute if price reached
                if random.random() < 0.6:
                    order['status'] = 'executed'
                    order['execution_price'] = order['price'] * (1 + random.uniform(-0.002, 0.002))
                else:
                    order['status'] = 'partial'
                    order['executed_quantity'] = order['quantity'] * random.uniform(0.3, 0.7)
                    
            elif order['type'] == 'twap':
                # Execute one slice
                slices_left = order.get('slices_remaining', order['slices'])
                if slices_left > 0:
                    order['slices_remaining'] = slices_left - 1
                    order['executed_quantity'] = order.get('executed_quantity', 0) + order['slice_quantity']
                    
                    if slices_left <= 1:
                        order['status'] = 'executed'
                        
            elif order['type'] == 'iceberg':
                # Execute visible portion
                visible = order['visible_quantity']
                order['executed_quantity'] = order.get('executed_quantity', 0) + visible
                order['remaining_quantity'] = order['quantity'] - order['executed_quantity']
                
                if order['remaining_quantity'] <= 0:
                    order['status'] = 'executed'
                    
            else:  # market
                order['status'] = 'executed'
                order['execution_price'] = await self.get_current_price(order['token'])
                
            # Move to executed if complete
            if order['status'] in ['executed', 'cancelled']:
                self.executed_orders.append(order)
                self.pending_orders.remove(order)
                
    async def update_order_status(self):
        """Update order status"""
        pass
        
    async def get_current_price(self, token: str) -> float:
        """Get current price of token"""
        # In production, fetch from oracle
        prices = {
            'SOL': 160.0,
            'ETH': 3500.0,
            'BTC': 61000.0,
            'BNB': 600.0,
            'AVAX': 40.0,
            'PAXG': 3960.0,
            'XAUT': 3965.0,
            'GOLD': 3960.0
        }
        return prices.get(token, 100.0)
        
    async def publish_execution_update(self):
        """Publish execution data update"""
        gold_holdings = await self.state_manager.get('gold_holdings', {})
        
        execution_data = {
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'recent_executions': self.executed_orders[-5:],
            'execution_stats': self.execution_stats,
            'gold_holdings': gold_holdings,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="profit_taking_execution_update",
            data=execution_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    # ============================================
    # GOLD SWAP STRATEGY – PAXG + XAUT
    # ============================================
    
    async def check_asset_availability(self, asset: str, amount: float) -> bool:
        """
        Check if asset is available for swap
        """
        asset_config = self.gold_config['assets'].get(asset)
        if not asset_config:
            return False
            
        # Check liquidity on available chains
        total_liquidity = 0
        for chain, chain_config in asset_config['chains'].items():
            liquidity = await self.get_asset_liquidity(asset.upper(), chain)
            total_liquidity += liquidity
            
        # Check price deviation
        current_price = await self.get_current_price(asset.upper())
        gold_price = await self.get_current_price('GOLD')
        
        deviation = abs(current_price - gold_price) / gold_price if gold_price > 0 else 1
        
        # Asset is available if:
        # 1. Total liquidity meets minimum
        # 2. Price deviation is within acceptable range
        return (total_liquidity >= asset_config['min_liquidity'] and
                deviation <= asset_config['max_deviation'])
        
    async def get_asset_liquidity(self, asset: str, chain: str) -> float:
        """
        Get liquidity for asset on specific chain
        """
        # Simulate liquidity
        liquidity = {
            'PAXG': {
                'solana': 5000000,
                'ethereum': 2000000,
                'bsc': 500000
            },
            'XAUT': {
                'ethereum': 1000000,
                'bsc': 300000
            }
        }
        return liquidity.get(asset, {}).get(chain, 0)
        
    async def find_best_platform_for_asset(self, usdt_amount: float, asset: str) -> Optional[Dict]:
        """
        Find best platform for specific asset
        """
        # Get supported platforms for this asset
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
                
            # Get metrics for this asset on this platform
            metrics = await self.get_platform_metrics_for_asset(
                name, platform, usdt_amount, asset
            )
            
            if metrics:
                candidates.append({
                    'name': name,
                    'chain': platform['chain'],
                    'asset': asset,
                    'metrics': metrics,
                    'total_cost': metrics['fees'] + metrics['slippage'] + metrics['gas_cost'],
                    'score': self.calculate_platform_score(metrics, usdt_amount)
                })
        
        if not candidates:
            return None
            
        candidates.sort(key=lambda x: (x['total_cost'], -x['score']))
        return candidates[0]
        
    async def get_platform_metrics_for_asset(self, name: str, platform: Dict, 
                                             amount: float, asset: str) -> Optional[Dict]:
        """
        Get real-time metrics for specific asset on specific platform
        """
        try:
            # Base metrics
            if platform['chain'] == 'solana':
                gas_cost = 0.01
                mev_protection = True
            elif platform['chain'] == 'bsc':
                gas_cost = 0.10
                mev_protection = False
            else:  # ethereum
                gas_cost = 5.00
                mev_protection = True
                
            # Asset-specific adjustments
            if asset == 'paxg':
                fee_rate = platform.get('fee', 0.002)
                slippage_rate = 0.001 if platform['chain'] == 'solana' else 0.0015
                liquidity = await self.get_asset_liquidity('PAXG', platform['chain'])
            else:  # xaut
                fee_rate = platform.get('fee', 0.003)
                slippage_rate = 0.0025
                liquidity = await self.get_asset_liquidity('XAUT', platform['chain'])
                
            fees = fee_rate * amount
            slippage = slippage_rate * amount
            
            # Adjust slippage if amount too large for liquidity
            if amount > liquidity * 0.1 and liquidity > 0:
                slippage *= (1 + (amount / liquidity))
                
            return {
                'fees': fees,
                'slippage': slippage,
                'gas_cost': gas_cost,
                'liquidity': liquidity,
                'execution_time': 0.5 if platform['chain'] == 'solana' else 1.0,
                'mev_protection': mev_protection
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return None
            
    def calculate_platform_score(self, metrics: Dict, amount: float) -> float:
        """
        Calculate platform score (0-100)
        """
        score = 0
        
        # Fees (max 30 points)
        fee_rate = metrics.get('fees', 0) / amount if amount > 0 else 0
        score += 30 * (1 - min(fee_rate / 0.01, 1))
        
        # Slippage (max 25 points)
        slippage_rate = metrics.get('slippage', 0) / amount if amount > 0 else 0
        score += 25 * (1 - min(slippage_rate / 0.01, 1))
        
        # Liquidity (max 20 points)
        liquidity = metrics.get('liquidity', 0)
        score += 20 * min(liquidity / 1000000, 1)
        
        # Gas cost (max 15 points)
        gas_cost = metrics.get('gas_cost', 10)
        score += 15 * (1 - min(gas_cost / 10, 1))
        
        # MEV protection (max 10 points)
        if metrics.get('mev_protection', False):
            score += 10
            
        return score
        
    async def execute_gold_swap(self, usdt_amount: float, 
                                preferred_asset: str = 'paxg',
                                preferred_chain: str = None) -> Dict:
        """
        Execute USDT → Gold swap
        preferred_asset: 'paxg' (default) or 'xaut'
        """
        logger.info(f"🚀 Executing USDT → {preferred_asset.upper()} swap for ${usdt_amount}")
        
        # Validate amount
        min_amount = self.gold_config['thresholds']['min_usdt_amount']
        if usdt_amount < min_amount:
            return {
                'status': 'failed',
                'reason': f'Amount ${usdt_amount} below minimum ${min_amount}'
            }
        
        # Check preferred asset availability
        asset_available = await self.check_asset_availability(preferred_asset, usdt_amount)
        
        if not asset_available and preferred_asset == 'paxg':
            # PAXG unavailable, try XAUT as fallback
            logger.warning("⚠️ PAXG unavailable, trying XAUT as fallback")
            preferred_asset = 'xaut'
            asset_available = await self.check_asset_availability(preferred_asset, usdt_amount)
            
        if not asset_available:
            return {
                'status': 'failed',
                'reason': f'Both PAXG and XAUT unavailable'
            }
            
        # Find best platform for this asset
        platform = await self.find_best_platform_for_asset(usdt_amount, preferred_asset)
        
        if not platform:
            return {
                'status': 'failed',
                'reason': f'No suitable platform found for {preferred_asset}'
            }
            
        # Check if need to split
        split_threshold = self.gold_config['thresholds']['split_threshold']
        if usdt_amount > split_threshold:
            return await self.execute_split_swap(usdt_amount, platform, preferred_asset)
        else:
            return await self.execute_single_swap(usdt_amount, platform, preferred_asset)
            
    async def execute_single_swap(self, usdt_amount: float, platform: Dict, asset: str) -> Dict:
        """
        Execute single swap on platform
        """
        try:
            # Get quote
            quote = await self.get_quote(usdt_amount, platform, asset)
            
            if not quote:
                return {
                    'status': 'failed',
                    'reason': 'Quote unavailable'
                }
                
            # Check slippage
            max_slippage = self.gold_config['thresholds']['max_single_slippage']
            if quote.get('slippage', 0) > max_slippage:
                return {
                    'status': 'failed',
                    'reason': f"Slippage {quote['slippage']*100:.2f}% > {max_slippage*100:.2f}%"
                }
                
            # Execute swap (simulate)
            asset_price = await self.get_current_price(asset.upper())
            asset_received = (usdt_amount / asset_price) * (1 - quote['slippage'])
            
            result = {
                'status': 'executed',
                'platform': platform['name'],
                'chain': platform['chain'],
                'asset': asset.upper(),
                'usdt_amount': usdt_amount,
                'asset_received': asset_received,
                'asset_price': asset_price,
                'fees': quote['fees'],
                'slippage': quote['slippage'],
                'gas_cost': quote['gas_cost'],
                'total_cost': quote['total_cost'],
                'tx_hash': f"0x{hash(str(datetime.now()))[:64]}",
                'timestamp': datetime.now().isoformat()
            }
            
            # Store result
            await self.store_gold_swap(result, asset)
            
            # Emit event
            await self.event_bus.publish(Event(
                event_type="gold_swap_executed",
                data=result,
                source=self.agent_id
            ))
            
            logger.info(f"✅ Swap executed: ${usdt_amount} → {asset_received:.4f} {asset.upper()}")
            
            return result
            
        except Exception as e:
            logger.error(f"Swap execution failed: {e}")
            return {
                'status': 'failed',
                'reason': str(e)
            }
            
    async def execute_split_swap(self, usdt_amount: float, platform: Dict, asset: str) -> Dict:
        """
        Split large swap into multiple orders
        """
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
                
        return {
            'status': 'executed',
            'platform': platform['name'],
            'chain': platform['chain'],
            'asset': asset.upper(),
            'total_usdt': usdt_amount,
            'total_asset': total_asset,
            'avg_price': usdt_amount / total_asset if total_asset > 0 else 0,
            'num_orders': len(results),
            'successful_orders': len([r for r in results if r['status'] == 'executed']),
            'failed_orders': len([r for r in results if r['status'] == 'failed']),
            'orders': results,
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_quote(self, usdt_amount: float, platform: Dict, asset: str) -> Optional[Dict]:
        """
        Get swap quote from platform
        """
        try:
            asset_price = await self.get_current_price(asset.upper())
            
            expected_asset = usdt_amount / asset_price if asset_price > 0 else 0
            
            # Calculate costs
            metrics = platform.get('metrics', {})
            fees = metrics.get('fees', 0)
            slippage = metrics.get('slippage', 0) / usdt_amount if usdt_amount > 0 else 0
            gas_cost = metrics.get('gas_cost', 0)
            
            return {
                'asset_price': asset_price,
                'expected_asset': expected_asset,
                'fees': fees,
                'slippage': slippage,
                'gas_cost': gas_cost,
                'total_cost': fees + slippage * usdt_amount + gas_cost,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None
            
    async def execute_stable_swap(self, asset: str = None, amount: float = None) -> Dict:
        """
        Swap Gold back to USDT (recovery)
        asset: 'paxg' or 'xaut' (None = all)
        """
        # Get gold holdings
        holdings = await self.state_manager.get('gold_holdings', {})
        
        # Determine what to swap
        if asset:
            assets_to_swap = {asset: holdings.get(asset, 0)}
        else:
            assets_to_swap = {
                'paxg': holdings.get('paxg', 0),
                'xaut': holdings.get('xaut', 0)
            }
            
        # Filter empty amounts
        assets_to_swap = {k: v for k, v in assets_to_swap.items() if v > 0}
        
        if not assets_to_swap:
            return {
                'status': 'failed',
                'reason': 'No gold holdings to swap'
            }
            
        results = []
        total_usdt = 0
        
        for asset_name, asset_amount in assets_to_swap.items():
            if amount and asset_name != asset:
                continue
                
            logger.info(f"🔄 Swapping {asset_amount} {asset_name.upper()} → USDT")
            
            # Find best platform
            usdt_value = asset_amount * await self.get_current_price(asset_name.upper())
            platform = await self.find_best_platform_for_asset(usdt_value, asset_name)
            
            if not platform:
                logger.warning(f"No platform for {asset_name}")
                continue
                
            # Execute swap
            asset_price = await self.get_current_price(asset_name.upper())
            usdt_received = asset_amount * asset_price * (1 - 0.002)
            
            result = {
                'status': 'executed',
                'platform': platform['name'],
                'chain': platform['chain'],
                'asset': asset_name.upper(),
                'asset_amount': asset_amount,
                'usdt_received': usdt_received,
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result)
            total_usdt += usdt_received
            
            # Clear from holdings
            holdings[asset_name] = 0
            
        # Update holdings
        await self.state_manager.set('gold_holdings', holdings)
        
        # Emit recovery event
        await self.event_bus.publish(Event(
            event_type="stable_recovery_executed",
            data={
                'total_usdt': total_usdt,
                'results': results,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        ))
        
        logger.info(f"✅ Recovery complete: ${total_usdt:.2f} USDT")
        
        return {
            'status': 'executed',
            'total_usdt': total_usdt,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    async def store_gold_swap(self, result: Dict, asset: str):
        """
        Store swap result in state
        """
        # Update gold holdings
        holdings = await self.state_manager.get('gold_holdings', {})
        holdings[asset] = holdings.get(asset, 0) + result.get('asset_received', 0)
        holdings['last_swap'] = result
        holdings['last_update'] = datetime.now().isoformat()
        await self.state_manager.set('gold_holdings', holdings)
        
        # Add to history
        history = await self.state_manager.get('gold_swap_history', [])
        history.append(result)
        if len(history) > 100:
            history = history[-100:]
        await self.state_manager.set('gold_swap_history', history)
        
    # ============================================
    # GOLD SWAP EVENT HANDLERS
    # ============================================
    
    async def handle_depeg(self, event: Event):
        """
        Handle depeg detection
        """
        logger.info(f"⚠️ Depeg detected! Event data: {event.data}")
        
        # Get stablecoin holdings
        holdings = await self.state_manager.get('wallet_1_holdings', {})
        usdt_amount = holdings.get('USDT', 0)
        usdc_amount = holdings.get('USDC', 0)
        
        total_stable = usdt_amount + usdc_amount
        
        if total_stable > self.gold_config['thresholds']['min_usdt_amount']:
            # Execute gold swap (PAXG first, fallback to XAUT)
            await self.execute_gold_swap(total_stable, preferred_asset='paxg')
        else:
            logger.info(f"Stable holdings ${total_stable} below minimum")
            
    async def handle_recovery(self, event: Event):
        """
        Handle stablecoin recovery
        """
        logger.info(f"✅ Stablecoins recovered! Event data: {event.data}")
        
        # Execute recovery swap (swap all)
        await self.execute_stable_swap()
        
    async def handle_swap_request(self, event: Event):
        """
        Handle manual swap request
        """
        amount = event.data.get('amount', 0)
        asset = event.data.get('asset', 'paxg')
        
        if amount > 0:
            await self.execute_gold_swap(amount, preferred_asset=asset)
        else:
            logger.warning("Invalid swap request amount")
            
    async def handle_stable_recovery_request(self, event: Event):
        """
        Handle stable recovery request
        """
        asset = event.data.get('asset', None)
        amount = event.data.get('amount', None)
        
        await self.execute_stable_swap(asset=asset, amount=amount)
        
    # ============================================
    # STATUS (UPDATED)
    # ============================================
        
    async def get_status(self) -> Dict[str, Any]:
        """Get profit taking executor status"""
        gold_holdings = await self.state_manager.get('gold_holdings', {})
        gold_history = await self.state_manager.get('gold_swap_history', [])
        
        # Check asset availability
        paxg_available = await self.check_asset_availability('paxg', 1000)
        xaut_available = await self.check_asset_availability('xaut', 1000)
        
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'execution_stats': self.execution_stats,
            'config': self.config,
            'gold_holdings': gold_holdings,
            'gold_swap_count': len(gold_history),
            'last_gold_swap': gold_history[-1] if gold_history else None,
            'gold_swap_enabled': True,
            'asset_availability': {
                'paxg': paxg_available,
                'xaut': xaut_available
            },
            'timestamp': datetime.now().isoformat()
        }
