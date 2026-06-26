"""
AlphaEdge Agent 23 – Execution Sniper
Order routing (Jito SG), limit/TWAP/VWAP/Iceberg on Jupiter/Raydium/Orca
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ExecutionSniper:
    """Execution Sniper – Optimized order routing and execution"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "sniper"
        self.running = False
        
        # Execution state
        self.pending_orders = []
        self.executed_orders = []
        self.order_history = []
        
        # Execution parameters
        self.slippage_tolerance = 0.01  # 1%
        self.min_order_size = 10  # Minimum in USD
        
        # DEX routing
        self.dexes = ['Jupiter', 'Raydium', 'Orca', 'Meteora']
        
    async def start(self):
        """Start the execution sniper"""
        logger.info("Execution Sniper starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("execution_request", self.handle_execution_request)
        await self.event_bus.subscribe("order_status_request", self.handle_order_status)
        await self.event_bus.subscribe("cancel_order_request", self.handle_cancel_order)
        
        # Start execution cycle
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
                # Process pending orders
                await self.process_pending_orders()
                
                # Update order status
                await self.update_order_status()
                
                # Publish execution update
                await self.publish_execution_update()
                
            except Exception as e:
                logger.error(f"Execution cycle error: {e}")
                
            await asyncio.sleep(1)  # Every second
            
    async def handle_execution_request(self, event: Event):
        """Handle execution requests"""
        if not self.running:
            return
            
        order = event.data.get('order')
        execution_type = order.get('type', 'limit')
        
        logger.info(f"Execution request: {order.get('token')} ({execution_type})")
        
        # Route to appropriate execution method
        if execution_type == 'limit':
            await self.execute_limit_order(order)
        elif execution_type == 'twap':
            await self.execute_twap_order(order)
        elif execution_type == 'vwap':
            await self.execute_vwap_order(order)
        elif execution_type == 'iceberg':
            await self.execute_iceberg_order(order)
        else:
            await self.execute_market_order(order)
            
    async def execute_limit_order(self, order: Dict):
        """Execute a limit order"""
        token = order.get('token')
        side = order.get('side', 'buy')
        price = order.get('price', 0)
        quantity = order.get('quantity', 0)
        
        # Validate order
        if quantity < self.min_order_size:
            logger.warning(f"Order too small: {quantity} < {self.min_order_size}")
            return
            
        # Find best DEX
        dex = await self.find_best_dex(token)
        
        # Execute order
        order_id = f"limit_{datetime.now().timestamp()}"
        
        result = {
            'order_id': order_id,
            'token': token,
            'side': side,
            'price': price,
            'quantity': quantity,
            'dex': dex,
            'status': 'executed',
            'execution_price': price,
            'timestamp': datetime.now().isoformat()
        }
        
        self.executed_orders.append(result)
        
        # Publish execution result
        response = Event(
            event_type="execution_result",
            data=result,
            source=self.agent_id,
            target=order.get('source')
        )
        await self.event_bus.publish(response)
        
        logger.info(f"Limit order executed: {token} @ {price}")
        
    async def execute_twap_order(self, order: Dict):
        """Execute a TWAP (Time-Weighted Average Price) order"""
        token = order.get('token')
        side = order.get('side', 'buy')
        total_quantity = order.get('quantity', 0)
        duration = order.get('duration', 60)  # seconds
        slices = order.get('slices', 5)
        
        slice_quantity = total_quantity / slices
        interval = duration / slices
        
        order_id = f"twap_{datetime.now().timestamp()}"
        
        for i in range(slices):
            # Execute each slice
            price = await self.get_current_price(token)
            
            result = {
                'order_id': f"{order_id}_{i}",
                'token': token,
                'side': side,
                'price': price,
                'quantity': slice_quantity,
                'dex': await self.find_best_dex(token),
                'status': 'executed',
                'execution_price': price,
                'slice': i + 1,
                'total_slices': slices,
                'timestamp': datetime.now().isoformat()
            }
            
            self.executed_orders.append(result)
            
            # Wait for next slice
            await asyncio.sleep(interval)
            
        # Publish final result
        response = Event(
            event_type="execution_result",
            data={
                'order_id': order_id,
                'token': token,
                'side': side,
                'total_quantity': total_quantity,
                'slices': slices,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=order.get('source')
        )
        await self.event_bus.publish(response)
        
        logger.info(f"TWAP order completed: {token}")
        
    async def execute_vwap_order(self, order: Dict):
        """Execute a VWAP (Volume-Weighted Average Price) order"""
        token = order.get('token')
        side = order.get('side', 'buy')
        quantity = order.get('quantity', 0)
        
        # Calculate VWAP based on volume profile
        volume_profile = await self.get_volume_profile(token)
        vwap_price = await self.calculate_vwap(token, volume_profile)
        
        # Execute at VWAP price
        order_id = f"vwap_{datetime.now().timestamp()}"
        
        result = {
            'order_id': order_id,
            'token': token,
            'side': side,
            'price': vwap_price,
            'quantity': quantity,
            'dex': await self.find_best_dex(token),
            'status': 'executed',
            'execution_price': vwap_price,
            'timestamp': datetime.now().isoformat()
        }
        
        self.executed_orders.append(result)
        
        # Publish result
        response = Event(
            event_type="execution_result",
            data=result,
            source=self.agent_id,
            target=order.get('source')
        )
        await self.event_bus.publish(response)
        
        logger.info(f"VWAP order executed: {token} @ {vwap_price}")
        
    async def execute_iceberg_order(self, order: Dict):
        """Execute an Iceberg order (hidden quantity)"""
        token = order.get('token')
        side = order.get('side', 'buy')
        total_quantity = order.get('quantity', 0)
        visible_quantity = order.get('visible', total_quantity * 0.1)
        
        order_id = f"iceberg_{datetime.now().timestamp()}"
        
        remaining = total_quantity
        while remaining > 0:
            slice_qty = min(visible_quantity, remaining)
            
            # Execute slice
            price = await self.get_current_price(token)
            
            result = {
                'order_id': f"{order_id}_{len(self.executed_orders)}",
                'token': token,
                'side': side,
                'price': price,
                'quantity': slice_qty,
                'dex': await self.find_best_dex(token),
                'status': 'executed',
                'execution_price': price,
                'remaining': remaining - slice_qty,
                'timestamp': datetime.now().isoformat()
            }
            
            self.executed_orders.append(result)
            remaining -= slice_qty
            
            # Wait between slices
            await asyncio.sleep(random.uniform(0.5, 2))
            
        # Publish final result
        response = Event(
            event_type="execution_result",
            data={
                'order_id': order_id,
                'token': token,
                'side': side,
                'total_quantity': total_quantity,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=order.get('source')
        )
        await self.event_bus.publish(response)
        
        logger.info(f"Iceberg order completed: {token}")
        
    async def execute_market_order(self, order: Dict):
        """Execute a market order"""
        token = order.get('token')
        side = order.get('side', 'buy')
        quantity = order.get('quantity', 0)
        
        # Get current market price
        price = await self.get_current_price(token)
        
        order_id = f"market_{datetime.now().timestamp()}"
        
        result = {
            'order_id': order_id,
            'token': token,
            'side': side,
            'price': price,
            'quantity': quantity,
            'dex': await self.find_best_dex(token),
            'status': 'executed',
            'execution_price': price,
            'slippage': random.uniform(0, 0.005),
            'timestamp': datetime.now().isoformat()
        }
        
        self.executed_orders.append(result)
        
        # Publish result
        response = Event(
            event_type="execution_result",
            data=result,
            source=self.agent_id,
            target=order.get('source')
        )
        await self.event_bus.publish(response)
        
        logger.info(f"Market order executed: {token} @ {price}")
        
    async def find_best_dex(self, token: str) -> str:
        """Find best DEX for token"""
        # In production, check liquidity across DEXes
        # For now, return random DEX
        return random.choice(self.dexes)
        
    async def get_current_price(self, token: str) -> float:
        """Get current price of token"""
        # In production, fetch from oracle
        # For now, return sample price
        prices = {
            'SOL': 160.0,
            'ETH': 3500.0,
            'BTC': 61000.0,
            'BNB': 600.0,
            'AVAX': 40.0
        }
        return prices.get(token, 100.0)
        
    async def get_volume_profile(self, token: str) -> Dict:
        """Get volume profile for VWAP calculation"""
        # In production, fetch from market data
        return {
            'volume_distribution': [0.1, 0.2, 0.3, 0.2, 0.1],
            'price_levels': [100, 101, 102, 103, 104]
        }
        
    async def calculate_vwap(self, token: str, volume_profile: Dict) -> float:
        """Calculate VWAP price"""
        # In production, use actual volume data
        price = await self.get_current_price(token)
        return price * (1 + random.uniform(-0.005, 0.005))
        
    async def process_pending_orders(self):
        """Process pending orders"""
        # In production, check order status and update
        pass
        
    async def update_order_status(self):
        """Update order status"""
        # In production, check execution status
        pass
        
    async def handle_order_status(self, event: Event):
        """Handle order status requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        
        # Find order
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
        
    async def handle_cancel_order(self, event: Event):
        """Handle cancel order requests"""
        if not self.running:
            return
            
        order_id = event.data.get('order_id')
        
        # In production, cancel order on DEX
        logger.info(f"Order cancellation requested: {order_id}")
        
        response = Event(
            event_type="order_cancel_response",
            data={
                'order_id': order_id,
                'cancelled': True,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_execution_update(self):
        """Publish execution data update"""
        execution_data = {
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'recent_orders': self.executed_orders[-5:],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="execution_update",
            data=execution_data,
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
            'active_dexes': self.dexes,
            'timestamp': datetime.now().isoformat()
        }
