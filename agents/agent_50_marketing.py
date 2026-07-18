"""
AlphaEdge Agent 50 – Marketing
Daily digest (12:00 UTC), entry posts, reposts, NEVER reveal bot holds
V13.0.7 – UPDATED with Scam Warning (Item 13)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import random

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MarketingAgent:
    """
    Marketing Agent – Manages marketing and communication
    V13.0.7 – Item 13: Scam Warning
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "marketing"
        self.running = False
        
        # Marketing configuration
        self.config = {
            'daily_digest_time': "12:00",
            'public_digest': True,
            'private_digest': True,
            'entry_posts': True,
            'never_reveal_holdings': True,
            'max_posts_per_day': 5
        }
        
        # ============================================
        # ITEM 13: SCAM WARNING CONFIGURATION
        # ============================================
        self.scam_warning_config = {
            'enabled': True,
            'post_daily': True,
            'post_weekly': True,
            'daily_time': "12:00",
            'weekly_day': "Monday",
            'weekly_time': "09:00",
            'message': """
⚠️ SCAM ALERT ⚠️

AlphaEdge NEVER asks for investment, runs paid ads, or solicits public funds.

If someone asks you for money using the AlphaEdge name:
❌ They are scammers
❌ Do not send any money
❌ Report them immediately

AlphaEdge is educational only.
No investment solicitation. No guaranteed returns.

#AlphaEdge #ScamAlert #CryptoEducation
""",
            'short_message': """
⚠️ SCAM ALERT: Anyone asking for money using AlphaEdge is a scammer.
We never ask for investment. Report immediately.
#AlphaEdge #ScamAlert
"""
        }
        
        # Scam warning state
        self.last_scam_warning = None
        self.last_weekly_warning = None
        
    async def start(self):
        """Start the marketing agent"""
        logger.info("Marketing Agent starting...")
        self.running = True
        
        await self.event_bus.subscribe("marketing_request", self.handle_marketing_request)
        await self.event_bus.subscribe("entry_signal", self.handle_entry_signal)
        
        asyncio.create_task(self.run_marketing_cycle())
        logger.info("Marketing Agent running")
        
    async def stop(self):
        """Stop the marketing agent"""
        self.running = False
        logger.info("Marketing Agent stopped")
        
    async def run_marketing_cycle(self):
        """Run regular marketing cycle"""
        while self.running:
            try:
                await self.check_daily_digest()
                await self.check_scam_warning()
                await self.publish_marketing_status()
            except Exception as e:
                logger.error(f"Marketing cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 13: SCAM WARNING
    # ============================================
    
    async def check_scam_warning(self):
        """Check if scam warning should be posted"""
        if not self.scam_warning_config['enabled']:
            return
            
        now = datetime.now()
        
        # Daily warning
        if self.scam_warning_config['post_daily']:
            daily_time = datetime.strptime(self.scam_warning_config['daily_time'], "%H:%M").time()
            if now.hour == daily_time.hour and now.minute == daily_time.minute:
                if self.last_scam_warning is None or (now - self.last_scam_warning).days >= 1:
                    await self.post_scam_warning()
                    self.last_scam_warning = now
                    
        # Weekly warning
        if self.scam_warning_config['post_weekly']:
            weekly_day = self.scam_warning_config['weekly_day']
            weekly_time = datetime.strptime(self.scam_warning_config['weekly_time'], "%H:%M").time()
            
            if now.strftime("%A") == weekly_day and now.hour == weekly_time.hour and now.minute == weekly_time.minute:
                if self.last_weekly_warning is None or (now - self.last_weekly_warning).days >= 7:
                    await self.post_weekly_scam_warning()
                    self.last_weekly_warning = now
                    
    async def post_scam_warning(self):
        """Post daily scam warning"""
        logger.info("📢 Posting scam warning")
        
        message = self.scam_warning_config['message']
        
        # Post to social media platforms
        await self._post_to_twitter(message)
        await self._post_to_telegram(message)
        
        # Store state
        await self.state_manager.set('last_scam_warning', datetime.now().isoformat())
        
    async def post_weekly_scam_warning(self):
        """Post weekly pinned scam warning"""
        logger.info("📌 Posting weekly pinned scam warning")
        
        message = self.scam_warning_config['message']
        
        # Post pinned message
        await self._post_pinned_to_twitter(message)
        await self._post_pinned_to_telegram(message)
        
        # Store state
        await self.state_manager.set('last_weekly_scam_warning', datetime.now().isoformat())
        
    async def handle_scam_inquiry(self, user_id: str) -> str:
        """
        Handle scam inquiry from user
        Returns warning message
        """
        return self.scam_warning_config['short_message']
        
    # ============================================
    # PLATFORM POSTING (Simulated)
    # ============================================
    
    async def _post_to_twitter(self, message: str):
        """Post to Twitter"""
        # In production, implement Twitter API
        logger.info(f"🐦 Twitter: {message[:100]}...")
        
    async def _post_to_telegram(self, message: str):
        """Post to Telegram"""
        # In production, implement Telegram API
        logger.info(f"📱 Telegram: {message[:100]}...")
        
    async def _post_pinned_to_twitter(self, message: str):
        """Post pinned to Twitter"""
        logger.info(f"📌 Twitter Pinned: {message[:100]}...")
        
    async def _post_pinned_to_telegram(self, message: str):
        """Post pinned to Telegram"""
        logger.info(f"📌 Telegram Pinned: {message[:100]}...")
        
    # ============================================
    # DAILY DIGEST
    # ============================================
    
    async def check_daily_digest(self):
        """Check if daily digest should be sent"""
        now = datetime.now()
        digest_time = datetime.strptime(self.config['daily_digest_time'], "%H:%M").time()
        
        if now.hour == digest_time.hour and now.minute == digest_time.minute:
            await self.send_daily_digest()
            
    async def send_daily_digest(self):
        """Send daily digest"""
        logger.info("📊 Sending daily digest")
        
        # Generate digest content
        digest = await self._generate_daily_digest()
        
        # Send public digest (educational)
        if self.config['public_digest']:
            await self._post_public_digest(digest['public'])
            
        # Send private digest (full performance)
        if self.config['private_digest']:
            await self._post_private_digest(digest['private'])
            
    async def _generate_daily_digest(self) -> Dict[str, str]:
        """Generate daily digest content"""
        # In production, fetch real data
        return {
            'public': "📊 AlphaEdge Daily Digest\n\nEducational content only.",
            'private': "📊 AlphaEdge Daily Digest\n\nFull performance details."
        }
        
    async def _post_public_digest(self, content: str):
        """Post public digest"""
        logger.info(f"📢 Public Digest: {content[:100]}...")
        
    async def _post_private_digest(self, content: str):
        """Post private digest"""
        logger.info(f"🔒 Private Digest: {content[:100]}...")
        
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    async def handle_marketing_request(self, event: Event):
        """Handle marketing requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        action = event.data.get('action')
        
        response_data = {'request_id': request_id}
        
        if action == 'scam_warning':
            user_id = event.data.get('user_id')
            response_data['message'] = await self.handle_scam_inquiry(user_id)
        elif action == 'daily_digest':
            await self.send_daily_digest()
            response_data['status'] = 'sent'
        else:
            response_data['error'] = 'Unknown action'
            
        response = Event(
            event_type="marketing_response",
            data=response_data,
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_entry_signal(self, event: Event):
        """Handle entry signals for marketing"""
        if not self.running or not self.config['entry_posts']:
            return
            
        token = event.data.get('token')
        tps = event.data.get('tps', 0)
        
        # Educational entry post (never reveal holdings)
        post = f"📈 Entry signal detected\nTPS: {tps}/100\nEducational only. Not financial advice."
        await self._post_to_twitter(post)
        
    async def publish_marketing_status(self):
        """Publish marketing status"""
        status_data = {
            'last_scam_warning': self.last_scam_warning.isoformat() if self.last_scam_warning else None,
            'last_weekly_warning': self.last_weekly_warning.isoformat() if self.last_weekly_warning else None,
            'scam_warning_enabled': self.scam_warning_config['enabled'],
            'timestamp': datetime.now().isoformat()
        }
        event = Event(event_type="marketing_status", data=status_data, source=self.agent_id)
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get marketing agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'scam_warning_enabled': self.scam_warning_config['enabled'],
            'last_scam_warning': self.last_scam_warning.isoformat() if self.last_scam_warning else None,
            'last_weekly_warning': self.last_weekly_warning.isoformat() if self.last_weekly_warning else None,
            'timestamp': datetime.now().isoformat()
        }
