"""
AlphaEdge Agent 63 – Profit Taking Executor
Execute orders (market/limit/TWAP/iceberg), minimize slippage, hide from MEV
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProfitTakingExecutor:
    """Profit Taking Executor – Executes profit-taking orders with minimal slippage"""
    
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
        
    async def start(self):
        """Start the profit taking executor"""
        logger.info("Profit Taking Executor starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("profit_take_request", self.handle_profit_take_request)
        await self.event_bus.subscribe("order_status_request", self.handle_order_status_request)
        await self.event_bus.subscribe("execution_cancel_request", self.handle_execution_cancel)
        
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
        # In production, check actual order status
        pass
        
    async def get_current_price(self, token: str) -> float:
        """Get current price of token"""
        # In production, fetch from oracle
        prices = {
            'SOL': 160.0,
            'ETH': 3500.0,
            'BTC': 61000.0,
            'BNB': 600.0,
            'AVAX': 40.0
        }
        return prices.get(token, 100.0)
        
    async def publish_execution_update(self):
        """Publish execution data update"""
        execution_data = {
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'recent_executions': self.executed_orders[-5:],
            'execution_stats': self.execution_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="profit_taking_execution_update",
            data=execution_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get profit taking executor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'execution_stats': self.execution_stats,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
