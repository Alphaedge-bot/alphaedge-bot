"""
AlphaEdge Agent 27 – Multi-DEX Router
Routes orders across multiple DEXes for best execution
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MultiDEXRouter:
    """Multi-DEX Router – Routes orders across multiple DEXes for optimal execution"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "dex_router"
        self.running = False
        
        # DEX state
        self.dex_liquidity = {}
        self.dex_orders = {}
        self.route_history = []
        
        # Supported DEXes
        self.dexes = ['Jupiter', 'Raydium', 'Orca', 'Meteora', 'Serum']
        
        # Routing parameters
        self.slippage_tolerance = 0.01
        self.min_liquidity_threshold = 100000  # Minimum liquidity in USD
        
    async def start(self):
        """Start the multi-DEX router"""
        logger.info("Multi-DEX Router starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("route_request", self.handle_route_request)
        await self.event_bus.subscribe("dex_update", self.handle_dex_update)
        await self.event_bus.subscribe("order_routing_request", self.handle_order_routing)
        
        # Start routing cycle
        asyncio.create_task(self.run_routing_cycle())
        
        logger.info("Multi-DEX Router running")
        
    async def stop(self):
        """Stop the multi-DEX router"""
        self.running = False
        logger.info("Multi-DEX Router stopped")
        
    async def run_routing_cycle(self):
        """Run regular routing cycle"""
        while self.running:
            try:
                # Update DEX liquidity
                await self.update_dex_liquidity()
                
                # Process pending routes
                await self.process_routes()
                
                # Publish routing update
                await self.publish_routing_update()
                
            except Exception as e:
                logger.error(f"Routing cycle error: {e}")
                
            await asyncio.sleep(10)  # Every 10 seconds
            
    async def handle_route_request(self, event: Event):
        """Handle route requests"""
        if not self.running:
            return
            
        token = event.data.get('token')
        amount = event.data.get('amount')
        side = event.data.get('side', 'buy')
        
        logger.info(f"Route request: {side} {amount} of {token}")
        
        # Find optimal route
        route = await self.find_optimal_route(token, amount, side)
        
        # Send response
        response = Event(
            event_type="route_response",
            data={
                'token': token,
                'amount': amount,
                'side': side,
                'route': route,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def find_optimal_route(self, token: str, amount: float, side: str) -> Dict:
        """Find optimal route for a trade"""
        routes = []
        
        # Check each DEX for liquidity
        for dex in self.dexes:
            liquidity = await self.get_dex_liquidity(dex, token)
            
            if liquidity >= self.min_liquidity_threshold:
                # Calculate expected price
                price = await self.get_dex_price(dex, token, side)
                
                # Calculate slippage estimate
                slippage = self.estimate_slippage(amount, liquidity)
                
                routes.append({
                    'dex': dex,
                    'price': price,
                    'liquidity': liquidity,
                    'slippage': slippage,
                    'estimated_cost': amount * price * (1 + slippage),
                    'score': self.calculate_route_score(price, liquidity, slippage)
                })
                
        # Sort by score (higher = better)
        routes.sort(key=lambda x: x['score'], reverse=True)
        
        # Select best routes
        best_routes = routes[:3]  # Top 3 routes
        
        # If multiple routes, split order
        if len(best_routes) > 1:
            return await self.create_split_route(best_routes, amount)
        else:
            return {
                'strategy': 'single',
                'routes': best_routes,
                'total_estimated_cost': best_routes[0]['estimated_cost'] if best_routes else 0,
                'timestamp': datetime.now().isoformat()
            }
            
    async def get_dex_liquidity(self, dex: str, token: str) -> float:
        """Get liquidity for a token on a DEX"""
        # In production, fetch from DEX API
        # For now, return simulated liquidity
        if dex not in self.dex_liquidity:
            self.dex_liquidity[dex] = {}
            
        if token not in self.dex_liquidity[dex]:
            # Simulate liquidity
            base_liquidity = {
                'SOL': 1000000,
                'ETH': 500000,
                'BTC': 200000,
                'BNB': 300000,
                'AVAX': 100000
            }
            liquidity = base_liquidity.get(token, 100000) * random.uniform(0.5, 1.5)
            self.dex_liquidity[dex][token] = liquidity
            
        return self.dex_liquidity[dex][token]
        
    async def get_dex_price(self, dex: str, token: str, side: str) -> float:
        """Get price for a token on a DEX"""
        # In production, fetch from DEX API
        # For now, return simulated price
        base_price = {
            'SOL': 160.0,
            'ETH': 3500.0,
            'BTC': 61000.0,
            'BNB': 600.0,
            'AVAX': 40.0
        }
        
        # Add small variation per DEX
        variation = random.uniform(-0.01, 0.01)
        price = base_price.get(token, 100) * (1 + variation)
        
        # Adjust for side
        if side == 'buy':
            price *= (1 + random.uniform(0.001, 0.005))
        else:
            price *= (1 - random.uniform(0.001, 0.005))
            
        return price
        
    def estimate_slippage(self, amount: float, liquidity: float) -> float:
        """Estimate slippage for an order"""
        if liquidity <= 0:
            return 0.05  # 5% default
            
        # Smaller orders = lower slippage
        ratio = amount / liquidity
        slippage = min(0.05, ratio * 5)  # Max 5%
        
        return slippage
        
    def calculate_route_score(self, price: float, liquidity: float, slippage: float) -> float:
        """Calculate route score (higher = better)"""
        # Price factor (lower price = higher score)
        price_factor = 1 / (1 + price) if price > 0 else 0
        
        # Liquidity factor (higher liquidity = higher score)
        liquidity_factor = min(1, liquidity / 1000000)
        
        # Slippage factor (lower slippage = higher score)
        slippage_factor = 1 - slippage
        
        # Weighted score
        score = (price_factor * 0.3) + (liquidity_factor * 0.4) + (slippage_factor * 0.3)
        
        return score
        
    async def create_split_route(self, routes: List[Dict], total_amount: float) -> Dict:
        """Create a split route across multiple DEXes"""
        total_score = sum(r['score'] for r in routes)
        
        allocations = []
        remaining = total_amount
        
        for i, route in enumerate(routes):
            # Allocate based on score
            if i == len(routes) - 1:
                allocation = remaining  # Last one gets the rest
            else:
                allocation = (route['score'] / total_score) * total_amount * 0.8
                remaining -= allocation
                
            allocations.append({
                'dex': route['dex'],
                'price': route['price'],
                'amount': allocation,
                'slippage': route['slippage'],
                'estimated_cost': allocation * route['price'] * (1 + route['slippage'])
            })
            
        return {
            'strategy': 'split',
            'routes': routes,
            'allocations': allocations,
            'total_estimated_cost': sum(a['estimated_cost'] for a in allocations),
            'timestamp': datetime.now().isoformat()
        }
        
    async def update_dex_liquidity(self):
        """Update DEX liquidity data"""
        # In production, fetch from DEX APIs
        # For now, random updates
        for dex in self.dexes:
            if dex not in self.dex_liquidity:
                self.dex_liquidity[dex] = {}
                
            for token in ['SOL', 'ETH', 'BTC', 'BNB', 'AVAX']:
                base = 100000 * random.uniform(0.8, 1.2)
                self.dex_liquidity[dex][token] = base
                
    async def process_routes(self):
        """Process pending routes"""
        # Routes are processed in handle_route_request
        pass
        
    async def handle_order_routing(self, event: Event):
        """Handle order routing requests"""
        if not self.running:
            return
            
        order = event.data.get('order')
        
        # Route the order
        route = await self.find_optimal_route(
            order.get('token'),
            order.get('amount'),
            order.get('side', 'buy')
        )
        
        # Execute route
        execution_result = await self.execute_route(route)
        
        # Send response
        response = Event(
            event_type="order_routing_response",
            data={
                'order': order,
                'route': route,
                'execution': execution_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def execute_route(self, route: Dict) -> Dict:
        """Execute a routed order"""
        if route['strategy'] == 'single':
            # Single route execution
            return {
                'status': 'executed',
                'dex': route['routes'][0]['dex'],
                'price': route['routes'][0]['price'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Split route execution
            results = []
            for allocation in route.get('allocations', []):
                results.append({
                    'dex': allocation['dex'],
                    'amount': allocation['amount'],
                    'price': allocation['price'],
                    'timestamp': datetime.now().isoformat()
                })
                
            return {
                'status': 'executed',
                'strategy': 'split',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
    async def handle_dex_update(self, event: Event):
        """Handle DEX updates"""
        if not self.running:
            return
            
        dex = event.data.get('dex')
        liquidity = event.data.get('liquidity')
        
        if dex and liquidity is not None:
            if dex not in self.dex_liquidity:
                self.dex_liquidity[dex] = {}
            self.dex_liquidity[dex][event.data.get('token')] = liquidity
            
    async def publish_routing_update(self):
        """Publish routing data update"""
        routing_data = {
            'dexes': self.dexes,
            'liquidity': self.dex_liquidity,
            'route_history': self.route_history[-10:],
            'active_routes': len(self.route_history),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="routing_update",
            data=routing_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get multi-DEX router status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'dexes_monitored': len(self.dexes),
            'active_routes': len(self.route_history),
            'liquidity_sources': self.dexes,
            'timestamp': datetime.now().isoformat()
        }
