"""
AlphaEdge Agent 25 – Intent Abstractor
Convert swaps to intents, broadcast to solver networks (Jupiter)
V13.0.7 – UPDATED with Intent Routing for Slippage Killer (Item 27)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class IntentAbstractor:
    """
    Intent Abstractor – Convert swaps to intents for solver networks
    V13.0.7 – Item 27: Intent Routing for Slippage Killer
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "intent_abstractor"
        self.running = False
        
        # ============================================
        # ITEM 27: INTENT ROUTING CONFIGURATION
        # ============================================
        self.intent_config = {
            'enabled': True,
            'solver_networks': [
                {'name': 'jupiter', 'endpoint': 'https://quote-api.jup.ag/v6', 'priority': 1},
                {'name': '1inch', 'endpoint': 'https://api.1inch.io/v5.0', 'priority': 2},
                {'name': 'pancakeswap', 'endpoint': 'https://api.pancakeswap.finance', 'priority': 3}
            ],
            'intent_routing': {
                'enabled': True,
                'broadcast_mode': 'parallel',
                'max_broadcast_timeout': 5,
                'best_price_selection': True
            },
            'slippage_protection': {
                'enabled': True,
                'max_slippage': 0.005,
                'fallback_to_market': True
            }
        }
        
        # Intent state
        self.pending_intents = []
        self.executed_intents = []
        self.best_prices = {}
        
    async def start(self):
        """Start the intent abstractor"""
        logger.info("Intent Abstractor starting...")
        self.running = True
        
        await self.event_bus.subscribe("intent_request", self.handle_intent_request)
        await self.event_bus.subscribe("best_price_request", self.handle_best_price_request)
        
        asyncio.create_task(self.run_intent_cycle())
        logger.info("Intent Abstractor running")
        
    async def stop(self):
        """Stop the intent abstractor"""
        self.running = False
        logger.info("Intent Abstractor stopped")
        
    async def run_intent_cycle(self):
        """Run regular intent cycle"""
        while self.running:
            try:
                await self.process_intents()
                await self.update_best_prices()
                await self.publish_intent_status()
            except Exception as e:
                logger.error(f"Intent cycle error: {e}")
            await asyncio.sleep(1)
            
    # ============================================
    # ITEM 27: INTENT ROUTING
    # ============================================
    
    async def create_intent(self, order: Dict) -> Dict:
        """
        Create intent from order
        Item 27: Convert swap to intent
        """
        intent = {
            'intent_id': f'intent_{datetime.now().timestamp()}',
            'token_in': order.get('token_in'),
            'token_out': order.get('token_out'),
            'amount_in': order.get('amount', 0),
            'slippage_tolerance': self.intent_config['slippage_protection']['max_slippage'],
            'solver_deadline': datetime.now().timestamp() + 60,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Add intent metadata
        if order.get('side') == 'buy':
            intent['intent_type'] = 'swap_buy'
        else:
            intent['intent_type'] = 'swap_sell'
            
        self.pending_intents.append(intent)
        return intent
        
    async def broadcast_intents(self, intent: Dict) -> Dict:
        """
        Broadcast intent to solver networks
        Item 27: Broadcast to solver networks
        """
        if not self.intent_config['enabled']:
            return {'status': 'skipped', 'reason': 'Intent disabled'}
            
        results = {}
        best_price = None
        best_solver = None
        
        # Broadcast in parallel
        if self.intent_config['intent_routing']['broadcast_mode'] == 'parallel':
            tasks = []
            for solver in self.intent_config['solver_networks']:
                if not solver.get('enabled', True):
                    continue
                tasks.append(self._send_to_solver(solver, intent))
                
            solver_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(solver_results):
                solver_name = self.intent_config['solver_networks'][i]['name']
                if isinstance(result, Exception):
                    results[solver_name] = {'status': 'failed', 'error': str(result)}
                else:
                    results[solver_name] = result
                    if result.get('price') and (best_price is None or result['price'] > best_price):
                        best_price = result['price']
                        best_solver = solver_name
                        
            # Select best price
            if self.intent_config['intent_routing']['best_price_selection'] and best_solver:
                intent['selected_solver'] = best_solver
                intent['selected_price'] = best_price
                intent['status'] = 'broadcasted'
                
        return {
            'status': 'success',
            'intent_id': intent['intent_id'],
            'results': results,
            'best_solver': best_solver,
            'best_price': best_price
        }
        
    async def _send_to_solver(self, solver: Dict, intent: Dict) -> Dict:
        """Send intent to a specific solver"""
        # In production, actual API call to solver
        # Simulating for now
        import random
        
        # Simulate price differences between solvers
        base_price = 100
        price_variation = random.uniform(0.97, 1.03)
        price = base_price * price_variation
        
        return {
            'status': 'success',
            'solver': solver['name'],
            'price': price,
            'slippage': random.uniform(0.001, 0.005),
            'execution_time': random.uniform(0.5, 2.0),
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_best_price(self, token_in: str, token_out: str, amount: float) -> Dict:
        """
        Get best price from all solvers
        Item 27: Best-price execution
        """
        if not self.intent_config['enabled']:
            return {'price': amount, 'solver': 'direct'}
            
        # Create temporary intent
        temp_intent = {
            'token_in': token_in,
            'token_out': token_out,
            'amount_in': amount
        }
        
        # Get prices from all solvers
        results = []
        for solver in self.intent_config['solver_networks']:
            if not solver.get('enabled', True):
                continue
            result = await self._send_to_solver(solver, temp_intent)
            if result.get('status') == 'success':
                results.append(result)
                
        # Find best price
        best = min(results, key=lambda x: x['price']) if results else None
        
        return {
            'price': best['price'] if best else amount,
            'solver': best['solver'] if best else 'none',
            'slippage': best['slippage'] if best else 0,
            'all_prices': results,
            'timestamp': datetime.now().isoformat()
        }
        
    async def execute_intent(self, intent: Dict) -> Dict:
        """
        Execute intent with slippage protection
        Item 27: Execution with slippage protection
        """
        if not self.intent_config['slippage_protection']['enabled']:
            return {'status': 'executed', 'intent_id': intent['intent_id']}
            
        try:
            # Check slippage
            expected_price = intent.get('selected_price', 0)
            current_price = await self._get_current_price(intent['token_out'])
            
            slippage = abs(current_price - expected_price) / expected_price
            
            if slippage > self.intent_config['slippage_protection']['max_slippage']:
                logger.warning(f"Slippage exceeded: {slippage:.2%}")
                
                if self.intent_config['slippage_protection']['fallback_to_market']:
                    # Fallback to market order
                    return {
                        'status': 'executed_fallback',
                        'intent_id': intent['intent_id'],
                        'slippage': slippage,
                        'fallback': 'market_order'
                    }
                else:
                    return {
                        'status': 'failed',
                        'intent_id': intent['intent_id'],
                        'reason': f'Slippage exceeded: {slippage:.2%}'
                    }
                    
            # Execute at expected price
            return {
                'status': 'executed',
                'intent_id': intent['intent_id'],
                'price': current_price,
                'slippage': slippage,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Intent execution error: {e}")
            return {'status': 'failed', 'reason': str(e)}
            
    async def _get_current_price(self, token: str) -> float:
        """Get current price of token"""
        return 100.0  # Simulated
            
    async def process_intents(self):
        """Process pending intents"""
        for intent in self.pending_intents[:10]:
            if intent['status'] == 'pending':
                # Broadcast intent
                broadcast_result = await self.broadcast_intents(intent)
                if broadcast_result['status'] == 'success':
                    # Execute intent
                    execution_result = await self.execute_intent(intent)
                    if execution_result['status'] in ['executed', 'executed_fallback']:
                        intent['status'] = 'completed'
                        intent['execution'] = execution_result
                        self.executed_intents.append(intent)
                        self.pending_intents.remove(intent)
                        
    async def update_best_prices(self):
        """Update best prices for tracked pairs"""
        # In production, periodically update best prices
        pass
        
    async def publish_intent_status(self):
        """Publish intent status"""
        status_data = {
            'pending_intents': len(self.pending_intents),
            'executed_intents': len(self.executed_intents),
            'best_prices': self.best_prices,
            'intent_enabled': self.intent_config['enabled'],
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="intent_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_intent_request(self, event: Event):
        """Handle intent requests"""
        if not self.running:
            return
            
        order = event.data.get('order', {})
        request_id = event.data.get('request_id')
        
        # Create and broadcast intent
        intent = await self.create_intent(order)
        broadcast_result = await self.broadcast_intents(intent)
        
        response = Event(
            event_type="intent_response",
            data={
                'request_id': request_id,
                'intent': intent,
                'broadcast_result': broadcast_result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_best_price_request(self, event: Event):
        """Handle best price requests"""
        if not self.running:
            return
            
        token_in = event.data.get('token_in')
        token_out = event.data.get('token_out')
        amount = event.data.get('amount', 0)
        request_id = event.data.get('request_id')
        
        best_price = await self.get_best_price(token_in, token_out, amount)
        
        response = Event(
            event_type="best_price_response",
            data={
                'request_id': request_id,
                'best_price': best_price,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get intent abstractor status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'pending_intents': len(self.pending_intents),
            'executed_intents': len(self.executed_intents),
            'intent_enabled': self.intent_config['enabled'],
            'best_prices': self.best_prices,
            'timestamp': datetime.now().isoformat()
        }
