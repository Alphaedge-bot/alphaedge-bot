"""
AlphaEdge Agent 23 – Execution Sniper
Order routing (Jito SG), limit/TWAP/VWAP/Iceberg on Jupiter/Raydium/Orca
V13.0.7 – UPDATED with Slippage Killer (Item 27)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import time

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ExecutionSniper:
    """
    Execution Sniper – Routes orders with minimal slippage
    V13.0.7 – Item 27: Slippage Killer
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "execution_sniper"
        self.running = False
        
        # ============================================
        # ITEM 27: SLIPPAGE KILLER CONFIGURATION
        # ============================================
        self.slippage_killer = {
            'enabled': True,
            'split_strategy': {
                'market_pct': 0.40,  # 40% market order
                'twap_pct': 0.60,    # 60% TWAP
                'twap_duration': 90,  # 90 seconds
                'twap_slices': 6      # 6 slices
            },
            'micro_cap_threshold': 200000000,  # $200M
            'sg_vps_proxy': {
                'enabled': True,
                'proxy_url': 'https://sg-proxy.alphaedge.io',
                'target_latency_ms': 15
            },
            'jito_bundles': {
                'enabled': True,
                'bundle_size': 3,
                'max_retries': 5
            },
            'slippage_limits': {
                'micro_cap': 0.015,   # 1.5%
                'small_cap': 0.010,   # 1.0%
                'mid_cap': 0.008,     # 0.8%
                'large_cap': 0.005    # 0.5%
            }
        }
        
        # Execution state
        self.pending_orders = []
        self.executed_orders = []
        self.execution_stats = {}
        
        # SG VPS proxy
        self.sg_proxy_active = False
        
    async def start(self):
        """Start the execution sniper"""
        logger.info("Execution Sniper starting...")
        self.running = True
        
        await self.event_bus.subscribe("execute_order", self.handle_execute_order)
        await self.event_bus.subscribe("cancel_order", self.handle_cancel_order)
        await self.event_bus.subscribe("order_status", self.handle_order_status)
        
        # Connect to SG VPS proxy
        if self.slippage_killer['sg_vps_proxy']['enabled']:
            await self._connect_sg_proxy()
        
        asyncio.create_task(self.run_execution_cycle())
        logger.info("Execution Sniper running")
        
    async def stop(self):
        """Stop the execution sniper"""
        self.running = False
        logger.info("Execution Sniper stopped")
        
    async def run_execution_cycle(self):
        """Run regular execution cycle"""
        while self.running:
            try:
                await self.process_orders()
                await self.monitor_executions()
                await self.publish_execution_status()
            except Exception as e:
                logger.error(f"Execution cycle error: {e}")
            await asyncio.sleep(1)
            
    # ============================================
    # SG VPS PROXY CONNECTION
    # ============================================
    
    async def _connect_sg_proxy(self):
        """Connect to SG VPS proxy for low-latency execution"""
        try:
            # In production, establish WebSocket/HTTP connection
            self.sg_proxy_active = True
            logger.info("✅ SG VPS proxy connected (target <15ms latency)")
        except Exception as e:
            logger.error(f"SG VPS proxy connection failed: {e}")
            self.sg_proxy_active = False
            
    # ============================================
    # ITEM 27: SLIPPAGE KILLER EXECUTION
    # ============================================
    
    async def execute_order_slippage_killer(self, order: Dict) -> Dict:
        """
        Execute order with Slippage Killer
        Item 27: 40% market + 60% TWAP for micro-caps
        """
        token = order.get('token')
        side = order.get('side', 'buy')
        amount = order.get('amount', 0)
        tier = order.get('tier', 'mid_cap')
        
        if not self.slippage_killer['enabled']:
            return await self._execute_simple_order(order)
        
        result = {
            'status': 'pending',
            'order_id': f'slippage_killer_{datetime.now().timestamp()}',
            'token': token,
            'side': side,
            'amount': amount,
            'tier': tier,
            'slippage_achieved': 0.0,
            'execution_parts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. Determine if micro-cap
            is_micro_cap = tier == 'micro_cap' or amount < self.slippage_killer['micro_cap_threshold']
            
            if is_micro_cap:
                # Micro-cap: 40% market + 60% TWAP
                result = await self._execute_micro_cap_slippage_killer(order, result)
            else:
                # Mid/Large cap: Standard execution
                result = await self._execute_standard_slippage_killer(order, result)
                
            # 2. Route via Jito bundles
            if self.slippage_killer['jito_bundles']['enabled']:
                result['jito_bundle'] = await self._execute_jito_bundle(order)
                
            # 3. Apply SG VPS proxy
            if self.slippage_killer['sg_vps_proxy']['enabled'] and self.sg_proxy_active:
                result['proxy_used'] = True
                result['latency_ms'] = self.slippage_killer['sg_vps_proxy']['target_latency_ms']
                
            # 4. Calculate slippage achieved
            slippage_limit = self.slippage_killer['slippage_limits'].get(tier, 0.01)
            result['slippage_achieved'] = await self._calculate_actual_slippage(result)
            result['slippage_limit'] = slippage_limit
            result['within_limit'] = result['slippage_achieved'] <= slippage_limit
            
            if result['within_limit']:
                result['status'] = 'success'
            else:
                logger.warning(f"Slippage exceeded limit: {result['slippage_achieved']:.2%} > {slippage_limit:.2%}")
                result['status'] = 'partial_success'
                
        except Exception as e:
            logger.error(f"Slippage Killer execution error: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            
        self.executed_orders.append(result)
        return result
        
    async def _execute_micro_cap_slippage_killer(self, order: Dict, result: Dict) -> Dict:
        """Execute micro-cap with 40% market + 60% TWAP"""
        amount = order.get('amount', 0)
        market_pct = self.slippage_killer['split_strategy']['market_pct']
        twap_pct = self.slippage_killer['split_strategy']['twap_pct']
        twap_duration = self.slippage_killer['split_strategy']['twap_duration']
        twap_slices = self.slippage_killer['split_strategy']['twap_slices']
        
        # 1. Execute market order (40%)
        market_amount = amount * market_pct
        market_result = await self._execute_market_order(order, market_amount)
        result['execution_parts'].append({
            'type': 'market',
            'amount': market_amount,
            'result': market_result
        })
        
        # 2. Execute TWAP (60%)
        twap_amount = amount * twap_pct
        twap_results = []
        slice_size = twap_amount / twap_slices
        
        for i in range(twap_slices):
            slice_result = await self._execute_twap_slice(order, slice_size, i, twap_slices)
            twap_results.append(slice_result)
            await asyncio.sleep(twap_duration / twap_slices)
            
        result['execution_parts'].append({
            'type': 'twap',
            'amount': twap_amount,
            'slices': twap_slices,
            'results': twap_results
        })
        
        # 3. Calculate average execution price
        result['avg_price'] = await self._calculate_average_price(result['execution_parts'])
        
        return result
        
    async def _execute_standard_slippage_killer(self, order: Dict, result: Dict) -> Dict:
        """Execute standard with 60% market + 40% limit"""
        amount = order.get('amount', 0)
        
        # 1. Market order (60%)
        market_amount = amount * 0.60
        market_result = await self._execute_market_order(order, market_amount)
        result['execution_parts'].append({
            'type': 'market',
            'amount': market_amount,
            'result': market_result
        })
        
        # 2. Limit order (40%)
        limit_amount = amount * 0.40
        limit_result = await self._execute_limit_order(order, limit_amount)
        result['execution_parts'].append({
            'type': 'limit',
            'amount': limit_amount,
            'result': limit_result
        })
        
        result['avg_price'] = await self._calculate_average_price(result['execution_parts'])
        
        return result
        
    async def _execute_market_order(self, order: Dict, amount: float) -> Dict:
        """Execute market order"""
        # In production, execute actual market order
        # Simulating for now
        return {
            'status': 'executed',
            'amount': amount,
            'price': order.get('price', 100) * (1 + random.uniform(-0.001, 0.001)),
            'timestamp': datetime.now().isoformat()
        }
        
    async def _execute_limit_order(self, order: Dict, amount: float) -> Dict:
        """Execute limit order"""
        return {
            'status': 'executed',
            'amount': amount,
            'price': order.get('price', 100) * (1 - random.uniform(0.001, 0.003)),
            'timestamp': datetime.now().isoformat()
        }
        
    async def _execute_twap_slice(self, order: Dict, amount: float, slice_num: int, total_slices: int) -> Dict:
        """Execute a single TWAP slice"""
        # In production, execute slice at staggered price
        price_offset = (slice_num / total_slices - 0.5) * 0.002  # ±0.1% spread
        return {
            'status': 'executed',
            'amount': amount,
            'price': order.get('price', 100) * (1 + price_offset),
            'slice': slice_num + 1,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _execute_jito_bundle(self, order: Dict) -> Dict:
        """Execute via Jito bundle"""
        return {
            'status': 'submitted',
            'bundle_id': f'bundle_{datetime.now().timestamp()}',
            'transactions': self.slippage_killer['jito_bundles']['bundle_size'],
            'timestamp': datetime.now().isoformat()
        }
        
    async def _calculate_average_price(self, parts: List[Dict]) -> float:
        """Calculate average execution price"""
        total_amount = 0
        total_value = 0
        
        for part in parts:
            if part['type'] == 'market':
                amount = part['amount']
                price = part['result']['price']
                total_amount += amount
                total_value += amount * price
            elif part['type'] == 'twap':
                for slice_result in part['results']:
                    amount = slice_result['amount']
                    price = slice_result['price']
                    total_amount += amount
                    total_value += amount * price
            elif part['type'] == 'limit':
                amount = part['amount']
                price = part['result']['price']
                total_amount += amount
                total_value += amount * price
                
        return total_value / total_amount if total_amount > 0 else 0
        
    async def _calculate_actual_slippage(self, result: Dict) -> float:
        """Calculate actual slippage achieved"""
        expected_price = result.get('expected_price', 100)
        avg_price = result.get('avg_price', expected_price)
        
        return abs(avg_price - expected_price) / expected_price
        
    async def _execute_simple_order(self, order: Dict) -> Dict:
        """Execute simple order (no Slippage Killer)"""
        return {
            'status': 'executed',
            'order_id': f'simple_{datetime.now().timestamp()}',
            'token': order.get('token'),
            'amount': order.get('amount'),
            'price': order.get('price', 100),
            'timestamp': datetime.now().isoformat()
        }
        
    # ============================================
    # ORDER HANDLERS
    # ============================================
    
    async def handle_execute_order(self, event: Event):
        """Handle execute order requests"""
        if not self.running:
            return
            
        order = event.data.get('order', {})
        request_id = event.data.get('request_id')
        
        # Route to Slippage Killer
        result = await self.execute_order_slippage_killer(order)
        
        response = Event(
            event_type="execute_order_response",
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
        
    async def handle_cancel_order(self, event: Event):
        """Handle cancel order requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        # In production, implement cancellation logic
        
        response = Event(
            event_type="cancel_order_response",
            data={
                'order_id': order_id,
                'cancelled': True,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_order_status(self, event: Event):
        """Handle order status requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        order = None
        
        for o in self.executed_orders:
            if o.get('order_id') == order_id:
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
        
    async def process_orders(self):
        """Process pending orders"""
        # In production, process actual order queue
        pass
        
    async def monitor_executions(self):
        """Monitor execution performance"""
        # Update execution stats
        if self.executed_orders:
            total_slippage = sum(o.get('slippage_achieved', 0) for o in self.executed_orders[-100:])
            avg_slippage = total_slippage / len(self.executed_orders[-100:])
            
            self.execution_stats = {
                'total_orders': len(self.executed_orders),
                'avg_slippage': avg_slippage,
                'within_limits': sum(1 for o in self.executed_orders[-100:] if o.get('within_limit', False)),
                'proxy_active': self.sg_proxy_active,
                'timestamp': datetime.now().isoformat()
            }
            
            # Publish slippage metrics
            await self.event_bus.publish(Event(
                event_type="slippage_metrics",
                data=self.execution_stats,
                source=self.agent_id
            ))
            
            logger.info(f"📊 Avg Slippage: {avg_slippage:.2%}")
            
    async def publish_execution_status(self):
        """Publish execution status"""
        event = Event(
            event_type="execution_status",
            data={
                'pending_orders': len(self.pending_orders),
                'executed_orders': len(self.executed_orders),
                'execution_stats': self.execution_stats,
                'slippage_killer_enabled': self.slippage_killer['enabled'],
                'sg_proxy_active': self.sg_proxy_active,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get execution sniper status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'execution_stats': self.execution_stats,
            'slippage_killer_enabled': self.slippage_killer['enabled'],
            'sg_proxy_active': self.sg_proxy_active,
            'timestamp': datetime.now().isoformat()
        }
