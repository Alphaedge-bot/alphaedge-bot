"""
AlphaEdge Agent 72 – Command Interface
Telegram webhook, web dashboard, physical button, command confirmation flow
V13.0.7 – UPDATED with Scam Warning Command (Item 13)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class CommandInterface:
    """
    Command Interface – Handles user commands via Telegram/Web
    V13.0.7 – Item 13: Scam Warning Command
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "command_interface"
        self.running = False
        
        # Command registry
        self.commands = {
            'status': self.cmd_status,
            'balance': self.cmd_balance,
            'positions': self.cmd_positions,
            'performance': self.cmd_performance,
            'swap_gold': self.cmd_swap_gold,
            'gold_status': self.cmd_gold_status,
            'gold_price': self.cmd_gold_price,
            'swap_stable': self.cmd_swap_stable,
            'gold_swap_history': self.cmd_gold_swap_history,
            # ============================================
            # ITEM 13: SCAM WARNING COMMAND
            # ============================================
            'scam_warning': self.cmd_scam_warning,
            'scam_report': self.cmd_scam_report,
        }
        
    async def start(self):
        """Start the command interface"""
        logger.info("Command Interface starting...")
        self.running = True
        
        await self.event_bus.subscribe("command_request", self.handle_command_request)
        await self.event_bus.subscribe("telegram_message", self.handle_telegram_message)
        
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
                await self.publish_command_status()
            except Exception as e:
                logger.error(f"Command cycle error: {e}")
            await asyncio.sleep(30)
            
    # ============================================
    # ITEM 13: SCAM WARNING COMMANDS
    # ============================================
    
    async def cmd_scam_warning(self, args: list) -> Dict:
        """
        /scam_warning – Display scam warning
        Item 13: Scam Warning Command
        """
        warning = """
⚠️ SCAM ALERT ⚠️

AlphaEdge NEVER asks for investment, runs paid ads, or solicits public funds.

If someone asks you for money using the AlphaEdge name:
✅ They are scammers
✅ Do not send any money
✅ Report them immediately

AlphaEdge is educational only.
No investment solicitation. No guaranteed returns.

For more info: https://github.com/Alphaedge-bot/alphaedge-bot

#AlphaEdge #ScamAlert
"""
        
        return {
            'status': 'success',
            'message': warning,
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_scam_report(self, args: list) -> Dict:
        """
        /scam_report [details] – Report a scam attempt
        Item 13: Scam Reporting
        """
        if not args:
            return {
                'status': 'error',
                'message': 'Usage: /scam_report [details of the scam attempt]'
            }
        
        details = ' '.join(args)
        
        # Log the report
        await self.state_manager.set(f'scam_report_{datetime.now().timestamp()}', {
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'reported_by': 'user'
        })
        
        # Notify admin
        await self.event_bus.publish(Event(
            event_type="scam_report_received",
            data={
                'details': details,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        ))
        
        return {
            'status': 'success',
            'message': f'✅ Scam report received. Thank you for helping keep the community safe.\n\nDetails: {details}',
            'timestamp': datetime.now().isoformat()
        }
        
    async def handle_telegram_message(self, event: Event):
        """Handle Telegram messages"""
        if not self.running:
            return
            
        message = event.data.get('message', '')
        user_id = event.data.get('user_id')
        chat_id = event.data.get('chat_id')
        
        # Check for scam keywords
        scam_keywords = ['invest', 'fund', 'token sale', 'crowdfunding', 'guaranteed']
        if any(keyword in message.lower() for keyword in scam_keywords):
            # Auto-respond with scam warning
            warning = await self.cmd_scam_warning([])
            await self._send_telegram_message(chat_id, warning['message'])
            
        # Check for commands
        if message.startswith('/'):
            command_parts = message.split()
            command = command_parts[0][1:]  # Remove '/'
            args = command_parts[1:]
            
            if command in self.commands:
                result = await self.commands[command](args)
                await self._send_telegram_message(chat_id, result['message'])
                
    async def _send_telegram_message(self, chat_id: str, message: str):
        """Send Telegram message"""
        # In production, implement Telegram API
        logger.info(f"📱 Telegram to {chat_id}: {message[:100]}...")
        
    # ============================================
    # EXISTING COMMANDS (Preserved)
    # ============================================
    
    async def cmd_status(self, args: list) -> Dict:
        """/status – Bot status"""
        return {
            'status': 'success',
            'message': 'Bot is running. All systems operational.',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_balance(self, args: list) -> Dict:
        """/balance – Wallet balances"""
        return {
            'status': 'success',
            'message': 'Balance information (educational only).',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_positions(self, args: list) -> Dict:
        """/positions – Current positions"""
        return {
            'status': 'success',
            'message': 'Position information (educational only).',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_performance(self, args: list) -> Dict:
        """/performance – Bot performance"""
        return {
            'status': 'success',
            'message': 'Performance metrics (educational only).',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_swap_gold(self, args: list) -> Dict:
        """/swap_gold [amount] – Swap USDT to PAXG"""
        if len(args) < 1:
            return {
                'status': 'error',
                'message': 'Usage: /swap_gold [amount] [--chain solana|ethereum|bsc]'
            }
        return {
            'status': 'pending',
            'message': f'🔄 Swapping ${args[0]} USDT → PAXG',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_gold_status(self, args: list) -> Dict:
        """/gold_status – Check gold holdings"""
        return {
            'status': 'success',
            'message': 'Gold holdings information.',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_gold_price(self, args: list) -> Dict:
        """/gold_price – Check PAXG price"""
        return {
            'status': 'success',
            'message': 'PAXG: $3,960.00',
            'data': {'paxg_usd': 3960.00},
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_swap_stable(self, args: list) -> Dict:
        """/swap_stable [amount] – Swap PAXG back to USDT"""
        if len(args) < 1:
            return {
                'status': 'error',
                'message': 'Usage: /swap_stable [amount] (or "all")'
            }
        return {
            'status': 'pending',
            'message': f'🔄 Swapping {args[0]} PAXG → USDT',
            'timestamp': datetime.now().isoformat()
        }
        
    async def cmd_gold_swap_history(self, args: list) -> Dict:
        """/gold_swap_history – View swap history"""
        return {
            'status': 'success',
            'message': 'Gold swap history.',
            'data': [],
            'timestamp': datetime.now().isoformat()
        }
        
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_command_request(self, event: Event):
        """Handle command requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        command = event.data.get('command')
        args = event.data.get('args', [])
        
        if command in self.commands:
            result = await self.commands[command](args)
        else:
            result = {
                'status': 'error',
                'message': f'Unknown command: {command}'
            }
            
        response = Event(
            event_type="command_response",
            data={
                'request_id': request_id,
                'command': command,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def publish_command_status(self):
        """Publish command status"""
        status_data = {
            'commands_available': len(self.commands),
            'scam_warning_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="command_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get command interface status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'commands_available': len(self.commands),
            'scam_warning_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
