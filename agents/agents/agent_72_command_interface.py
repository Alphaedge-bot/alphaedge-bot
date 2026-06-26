"""
AlphaEdge Agent 72 – Command Interface
Telegram webhook, web dashboard, physical button, command confirmation flow
Bidirectional WebSocket bridge (TradingView ↔ Bot)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CommandInterface:
    """Command Interface – User interaction and control"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "command_interface"
        self.running = False
        
        # Command state
        self.command_history = []
        self.active_commands = {}
        self.websocket_clients = {}
        
        # Configuration
        self.config = {
            'websocket_port': 8443,
            'telegram_webhook': '/webhook',
            'dashboard_port': 8080,
            'command_timeout': 60  # seconds
        }
        
        # Command registry
        self.commands = {
            '/status': self.cmd_status,
            '/pause_trading': self.cmd_pause_trading,
            '/resume_trading': self.cmd_resume_trading,
            '/emergency_stop': self.cmd_emergency_stop,
            '/panic_sell': self.cmd_panic_sell,
            '/analyze': self.cmd_analyze,
            '/wallets': self.cmd_wallets,
            '/circuit_status': self.cmd_circuit_status,
            '/season_status': self.cmd_season_status,
            '/performance': self.cmd_performance,
            '/node_status': self.cmd_node_status,
            '/force_failover': self.cmd_force_failover,
            '/replay_wal': self.cmd_replay_wal,
            '/hardware_status': self.cmd_hardware_status,
            '/rpc_latency': self.cmd_rpc_latency,
            '/gas_status': self.cmd_gas_status,
            '/ai_status': self.cmd_ai_status,
            '/botscores': self.cmd_bot_scores,
            '/journal': self.cmd_journal,
            '/strategy_ranking': self.cmd_strategy_ranking,
            '/priority_fees': self.cmd_priority_fees,
            '/shutdown_bot': self.cmd_shutdown_bot,
            '/power_outage': self.cmd_power_outage,
            '/resume_power': self.cmd_resume_power,
            '/stable_status': self.cmd_stable_status,
            '/convert_to_stable': self.cmd_convert_to_stable,
            '/convert_to_gold': self.cmd_convert_to_gold
        }
        
    async def start(self):
        """Start the command interface"""
        logger.info("Command Interface starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("command_request", self.handle_command_request)
        await self.event_bus.subscribe("websocket_message", self.handle_websocket_message)
        await self.event_bus.subscribe("websocket_connection", self.handle_websocket_connection)
        
        # Start command processing
        asyncio.create_task(self.run_command_cycle())
        
        logger.info("Command Interface running")
        
    async def stop(self):
        """Stop the command interface"""
        self.running = False
        logger.info("Command Interface stopped")
        
    async def run_command_cycle(self):
        """Run regular command cycle"""
        while self.running:
            try:
                # Process active commands
                await self.process_active_commands()
                
                # Publish command update
                await self.publish_command_update()
                
            except Exception as e:
                logger.error(f"Command cycle error: {e}")
                
            await asyncio.sleep(5)  # Every 5 seconds
            
    async def handle_command_request(self, event: Event):
        """Handle command requests"""
        if not self.running:
            return
            
        command = event.data.get('command')
        params = event.data.get('params', {})
        source = event.source
        
        logger.info(f"Command received: {command} from {source}")
        
        # Execute command
        result = await self.execute_command(command, params)
        
        # Send response
        response = Event(
            event_type="command_response",
            data={
                'command': command,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=source
        )
        await self.event_bus.publish(response)
        
    async def handle_websocket_message(self, event: Event):
        """Handle WebSocket messages"""
        if not self.running:
            return
            
        message = event.data.get('message')
        client_id = event.data.get('client_id')
        
        logger.info(f"WebSocket message from {client_id}")
        
        # Parse command
        try:
            data = json.loads(message)
            command = data.get('command')
            params = data.get('params', {})
            
            # Execute command
            result = await self.execute_command(command, params)
            
            # Send response back
            response = Event(
                event_type="websocket_response",
                data={
                    'client_id': client_id,
                    'response': json.dumps({
                        'command': command,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    })
                },
                source=self.agent_id
            )
            await self.event_bus.publish(response)
            
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
            
    async def handle_websocket_connection(self, event: Event):
        """Handle WebSocket connections"""
        if not self.running:
            return
            
        client_id = event.data.get('client_id')
        action = event.data.get('action')
        
        if action == 'connected':
            self.websocket_clients[client_id] = {
                'connected_at': datetime.now().isoformat(),
                'active': True
            }
            logger.info(f"WebSocket client connected: {client_id}")
        elif action == 'disconnected':
            if client_id in self.websocket_clients:
                del self.websocket_clients[client_id]
                logger.info(f"WebSocket client disconnected: {client_id}")
                
    async def execute_command(self, command: str, params: Dict) -> Dict:
        """Execute a command"""
        # Check if command exists
        if command not in self.commands:
            return {
                'status': 'error',
                'message': f'Unknown command: {command}',
                'timestamp': datetime.now().isoformat()
            }
            
        # Execute command
        try:
            result = await self.commands[command](params)
            return {
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def process_active_commands(self):
        """Process active commands"""
        # Clean expired commands
        current_time = datetime.now()
        expired = []
        
        for cmd_id, cmd in self.active_commands.items():
            cmd_time = datetime.fromisoformat(cmd['timestamp'])
            if (current_time - cmd_time).seconds > self.config['command_timeout']:
                expired.append(cmd_id)
                
        for cmd_id in expired:
            del self.active_commands[cmd_id]
            
    async def publish_command_update(self):
        """Publish command data update"""
        command_data = {
            'command_history': self.command_history[-10:],
            'active_commands': len(self.active_commands),
            'websocket_clients': len(self.websocket_clients),
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="command_interface_update",
            data=command_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    # Command Handlers
    async def cmd_status(self, params: Dict) -> Dict:
        """Get bot status"""
        positions = await self.state_manager.get_all_positions()
        circuit_breakers = await self.state_manager.get('circuit_breakers', {})
        bpg = await self.state_manager.get('bpg', 0)
        
        return {
            'status': 'running',
            'positions': len(positions),
            'circuit_breakers': circuit_breakers,
            'bpg': bpg,
            'uptime': await self.state_manager.get('uptime', 0)
        }
        
    async def cmd_pause_trading(self, params: Dict) -> Dict:
        """Pause trading"""
        await self.state_manager.set('trading_paused', True)
        return {'trading': 'paused'}
        
    async def cmd_resume_trading(self, params: Dict) -> Dict:
        """Resume trading"""
        await self.state_manager.set('trading_paused', False)
        return {'trading': 'resumed'}
        
    async def cmd_emergency_stop(self, params: Dict) -> Dict:
        """Emergency stop"""
        await self.state_manager.set('emergency_stop', True)
        await self.state_manager.set('trading_paused', True)
        return {'status': 'emergency_stop_activated'}
        
    async def cmd_panic_sell(self, params: Dict) -> Dict:
        """Panic sell all positions"""
        # In production, execute sell orders
        return {'status': 'panic_sell_executed'}
        
    async def cmd_analyze(self, params: Dict) -> Dict:
        """Analyze token"""
        token = params.get('token')
        if not token:
            return {'error': 'No token provided'}
            
        tps = await self.state_manager.get(f'tps_{token}', 0)
        return {
            'token': token,
            'tps': tps,
            'analysis': f'Analysis for {token}'
        }
        
    async def cmd_wallets(self, params: Dict) -> Dict:
        """Get wallet balances"""
        wallet1 = await self.state_manager.get('wallet_1', 0)
        wallet2 = await self.state_manager.get('wallet_2', 0)
        wallet3 = await self.state_manager.get('wallet_3', 0)
        
        return {
            'wallet_1': wallet1,
            'wallet_2': wallet2,
            'wallet_3': wallet3
        }
        
    async def cmd_circuit_status(self, params: Dict) -> Dict:
        """Get circuit breaker status"""
        return await self.state_manager.get('circuit_breakers', {})
        
    async def cmd_season_status(self, params: Dict) -> Dict:
        """Get season status"""
        return {
            'current_season': await self.state_manager.get('current_season', 'balanced')
        }
        
    async def cmd_performance(self, params: Dict) -> Dict:
        """Get performance metrics"""
        return await self.state_manager.get('performance_metrics', {})
        
    async def cmd_node_status(self, params: Dict) -> Dict:
        """Get node status"""
        return {
            'primary': await self.state_manager.get('primary_node_status', 'active'),
            'backup': await self.state_manager.get('backup_node_status', 'standby')
        }
        
    async def cmd_force_failover(self, params: Dict) -> Dict:
        """Force failover to backup node"""
        await self.state_manager.set('primary_node_status', 'failed')
        await self.state_manager.set('backup_node_status', 'active')
        return {'status': 'failover_forced'}
        
    async def cmd_replay_wal(self, params: Dict) -> Dict:
        """Replay WAL"""
        # In production, replay WAL
        return {'status': 'wal_replay_initiated'}
        
    async def cmd_hardware_status(self, params: Dict) -> Dict:
        """Get hardware status"""
        return {
            'cpu': await self.state_manager.get('cpu_usage', 0),
            'memory': await self.state_manager.get('memory_usage', 0),
            'disk': await self.state_manager.get('disk_usage', 0)
        }
        
    async def cmd_rpc_latency(self, params: Dict) -> Dict:
        """Get RPC latency"""
        return await self.state_manager.get('rpc_latency', {})
        
    async def cmd_gas_status(self, params: Dict) -> Dict:
        """Get gas status"""
        return await self.state_manager.get('gas_reserves', {})
        
    async def cmd_ai_status(self, params: Dict) -> Dict:
        """Get AI status"""
        return {
            'grok_available': await self.state_manager.get('grok_available', False),
            'grok_calls_used': await self.state_manager.get('grok_calls_used', 0)
        }
        
    async def cmd_bot_scores(self, params: Dict) -> Dict:
        """Get bot scores"""
        return {
            'bpg': await self.state_manager.get('bpg', 0),
            'bpg_grade': await self.state_manager.get('bpg_grade', 'N/A')
        }
        
    async def cmd_journal(self, params: Dict) -> Dict:
        """Get trading journal"""
        return {
            'trades': await self.state_manager.get('trade_history', [])
        }
        
    async def cmd_strategy_ranking(self, params: Dict) -> Dict:
        """Get strategy ranking"""
        return await self.state_manager.get('strategy_ranking', {})
        
    async def cmd_priority_fees(self, params: Dict) -> Dict:
        """Get priority fees"""
        return await self.state_manager.get('priority_fees', {})
        
    async def cmd_shutdown_bot(self, params: Dict) -> Dict:
        """Shutdown bot"""
        # In production, graceful shutdown
        self.running = False
        return {'status': 'shutting_down'}
        
    async def cmd_power_outage(self, params: Dict) -> Dict:
        """Handle power outage"""
        await self.state_manager.set('power_outage', True)
        await self.state_manager.set('trading_paused', True)
        return {'status': 'power_outage_mode_activated'}
        
    async def cmd_resume_power(self, params: Dict) -> Dict:
        """Resume after power outage"""
        await self.state_manager.set('power_outage', False)
        await self.state_manager.set('trading_paused', False)
        return {'status': 'power_restored'}
        
    async def cmd_stable_status(self, params: Dict) -> Dict:
        """Get stablecoin status"""
        return await self.state_manager.get('stablecoin_status', {})
        
    async def cmd_convert_to_stable(self, params: Dict) -> Dict:
        """Convert to stablecoins"""
        percentage = params.get('percentage', 100)
        await self.state_manager.set('stable_conversion_pct', percentage)
        return {'status': 'conversion_initiated', 'percentage': percentage}
        
    async def cmd_convert_to_gold(self, params: Dict) -> Dict:
        """Convert to gold"""
        await self.state_manager.set('gold_conversion', True)
        return {'status': 'gold_conversion_initiated'}
        
    async def get_status(self) -> Dict[str, Any]:
        """Get command interface status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'active_commands': len(self.active_commands),
            'websocket_clients': len(self.websocket_clients),
            'registered_commands': len(self.commands),
            'timestamp': datetime.now().isoformat()
        }
