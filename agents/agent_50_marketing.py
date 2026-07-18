"""
AlphaEdge Agent 50 – Marketing
Daily digest (12:00 UTC), entry posts, reposts, NEVER reveal bot holds
V13.0.7 – UPDATED with Marketing Enhancements (Item 11)
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
    V13.0.7 – Item 11: Marketing Enhancements
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
        
        # ============================================
        # ITEM 11: MARKETING ENHANCEMENTS
        # ============================================
        self.marketing_enhancements = {
            'momentum_boost': {
                'enabled': True,
                'threshold': 10,  # TPS increase threshold
                'emoji': '⚡'
            },
            'entry_breakdown': {
                'enabled': True,
                'show_signals': True,
                'show_zone': True,
                'show_tps': True
            },
            'streak_tracking': {
                'enabled': True,
                'show_wins': True,
                'show_losses': False
            },
            'daily_highlights': {
                'enabled': True,
                'show_best_setup': True
            }
        }
        
        # Marketing state
        self.last_scam_warning = None
        self.last_weekly_warning = None
        self.last_momentum_post = None
        self.streak_count = 0
        self.daily_posts = 0
        
    async def start(self):
        """Start the marketing agent"""
        logger.info("Marketing Agent starting...")
        self.running = True
        
        await self.event_bus.subscribe("marketing_request", self.handle_marketing_request)
        await self.event_bus.subscribe("entry_signal", self.handle_entry_signal)
        await self.event_bus.subscribe("tps_update", self.handle_tps_update)
        
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
                await self.check_momentum_boost()
                await self.publish_marketing_status()
            except Exception as e:
                logger.error(f"Marketing cycle error: {e}")
            await asyncio.sleep(60)
            
    # ============================================
    # ITEM 11: MOMENTUM BOOST DISPLAY
    # ============================================
    
    async def check_momentum_boost(self):
        """Check for momentum boost opportunities"""
        if not self.marketing_enhancements['momentum_boost']['enabled']:
            return
            
        # Get recent TPS history
        tps_history = await self.state_manager.get('tps_history', [])
        if len(tps_history) < 2:
            return
            
        current_tps = tps_history[-1]
        previous_tps = tps_history[-2]
        increase = current_tps - previous_tps
        
        if increase >= self.marketing_enhancements['momentum_boost']['threshold']:
            await self.post_momentum_boost(current_tps, previous_tps, increase)
            
    async def post_momentum_boost(self, current_tps: float, previous_tps: float, increase: float):
        """Post momentum boost content"""
        emoji = self.marketing_enhancements['momentum_boost']['emoji']
        
        content = f"""
{emoji} TPS MOMENTUM BOOST

TPS: {previous_tps:.0f} → {current_tps:.0f} (+{increase:.0f})

📈 Signal: Strong momentum detected
📍 Zone: Elite support confirmation

📚 Education: TPS increase indicates improving market conditions.
⚠️ Educational only. Not financial advice.

#AlphaEdge #TradingEducation
"""
        await self._post_to_twitter(content)
        await self._post_to_telegram(content)
        self.last_momentum_post = datetime.now().isoformat()
        
    # ============================================
    # ITEM 11: ENTRY BREAKDOWN
    # ============================================
    
    async def post_entry_breakdown(self, entry_data: Dict):
        """Post detailed entry breakdown"""
        if not self.marketing_enhancements['entry_breakdown']['enabled']:
            return
            
        token = entry_data.get('token', 'Unknown')
        tps = entry_data.get('tps', 0)
        zone = entry_data.get('zone', 'Standard')
        signals = entry_data.get('signals', [])
        
        content = f"""
🎯 ENTRY BREAKDOWN

🟢 TPS: {tps:.0f}/100 ({'STRONG BUY' if tps >= 82 else 'MONITOR'})
📍 Zone: {zone}
📊 Signals: {', '.join(signals[:3])}

📚 Education: {await self._generate_entry_education(entry_data)}
⚠️ Educational only. Not financial advice.

#AlphaEdge #ICT #SMC
"""
        await self._post_to_twitter(content)
        await self._post_to_telegram(content)
        
    async def _generate_entry_education(self, entry_data: Dict) -> str:
        """Generate educational content for entry"""
        tps = entry_data.get('tps', 0)
        if tps >= 82:
            return "High TPS indicates strong confluence. Multiple signals aligned."
        elif tps >= 70:
            return "Moderate TPS. Core signals present. Monitor for confirmation."
        else:
            return "Low TPS. Wait for additional signals before consideration."
            
    # ============================================
    # ITEM 11: STREAK TRACKING
    # ============================================
    
    async def update_streak(self, win: bool):
        """Update winning/losing streak"""
        if win:
            self.streak_count = self.streak_count + 1 if self.streak_count > 0 else 1
        else:
            self.streak_count = self.streak_count - 1 if self.streak_count < 0 else -1
            
        if self.marketing_enhancements['streak_tracking']['enabled']:
            if abs(self.streak_count) >= 3:
                await self.post_streak_update()
                
    async def post_streak_update(self):
        """Post streak update"""
        if self.streak_count > 0:
            emoji = "🔥"
            status = f"{self.streak_count} WINS IN A ROW"
            color = "🟢"
        else:
            emoji = "❄️"
            status = f"{abs(self.streak_count)} LOSSES IN A ROW"
            color = "🔴"
            
        content = f"""
{emoji} STREAK UPDATE

{color} {status}

📊 Current streak: {self.streak_count}

📚 Education: Trading streaks are normal. Risk management is key.
⚠️ Educational only. Not financial advice.

#AlphaEdge #Trading
"""
        await self._post_to_twitter(content)
        
    # ============================================
    # ITEM 11: DAILY HIGHLIGHTS
    # ============================================
    
    async def generate_daily_highlights(self) -> str:
        """Generate daily highlights"""
        if not self.marketing_enhancements['daily_highlights']['enabled']:
            return ""
            
        # Get best setup of the day
        setups = await self.state_manager.get('daily_setups', [])
        if not setups:
            return ""
            
        best = max(setups, key=lambda x: x.get('tps', 0))
        
        content = f"""
🏆 TODAY'S BEST SETUP

TPS: {best.get('tps', 0):.0f}/100
Token: {best.get('token', 'Unknown')}
Zone: {best.get('zone', 'Standard')}

📚 Education: Best setup of the day based on confluence scoring.

#AlphaEdge #Trading
"""
        return content
        
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
        await self._post_to_twitter(self.scam_warning_config['message'])
        await self._post_to_telegram(self.scam_warning_config['message'])
        await self.state_manager.set('last_scam_warning', datetime.now().isoformat())
        
    async def post_weekly_scam_warning(self):
        """Post weekly pinned scam warning"""
        logger.info("📌 Posting weekly pinned scam warning")
        await self._post_pinned_to_twitter(self.scam_warning_config['message'])
        await self._post_pinned_to_telegram(self.scam_warning_config['message'])
        await self.state_manager.set('last_weekly_scam_warning', datetime.now().isoformat())
        
    async def handle_scam_inquiry(self, user_id: str) -> str:
        """Handle scam inquiry from user"""
        return self.scam_warning_config['short_message']
        
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
        """Send daily digest with enhanced content"""
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
        """Generate daily digest content with enhancements"""
        # Get metrics
        metrics = await self.state_manager.get('performance_metrics', {})
        
        # Generate highlights
        highlights = await self.generate_daily_highlights()
        
        public_content = f"""
📊 ALPHAEDGE DAILY DIGEST

📈 Today's Market Overview
DXY: {await self._get_dxy():.2f}
BTC: ${await self._get_btc():,.0f}
Regime: {await self._get_regime()}

{highlights}

📚 Education: {await self._get_daily_education()}
⚠️ Educational only. Not financial advice.

#AlphaEdge #CryptoEducation
"""
        
        private_content = f"""
📊 ALPHAEDGE DAILY DIGEST (PRIVATE)

📈 Performance Metrics
Win Rate: {metrics.get('win_rate', 0)*100:.1f}%
Profit Factor: {metrics.get('profit_factor', 0):.2f}
Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
Max Drawdown: {metrics.get('max_drawdown', 0)*100:.1f}%

{highlights}

📊 Positions: {await self._get_position_summary()}
"""
        return {'public': public_content, 'private': private_content}
        
    # ============================================
    # PLATFORM POSTING (Simulated)
    # ============================================
    
    async def _post_to_twitter(self, message: str):
        """Post to Twitter"""
        logger.info(f"🐦 Twitter: {message[:100]}...")
        
    async def _post_to_telegram(self, message: str):
        """Post to Telegram"""
        logger.info(f"📱 Telegram: {message[:100]}...")
        
    async def _post_pinned_to_twitter(self, message: str):
        """Post pinned to Twitter"""
        logger.info(f"📌 Twitter Pinned: {message[:100]}...")
        
    async def _post_pinned_to_telegram(self, message: str):
        """Post pinned to Telegram"""
        logger.info(f"📌 Telegram Pinned: {message[:100]}...")
        
    async def _post_public_digest(self, content: str):
        """Post public digest"""
        logger.info(f"📢 Public Digest: {content[:100]}...")
        
    async def _post_private_digest(self, content: str):
        """Post private digest"""
        logger.info(f"🔒 Private Digest: {content[:100]}...")
        
    # ============================================
    # HELPERS
    # ============================================
    
    async def _get_dxy(self) -> float:
        return 100.69
        
    async def _get_btc(self) -> float:
        return 63836.07
        
    async def _get_regime(self) -> str:
        return "BULL"
        
    async def _get_daily_education(self) -> str:
        return "Today's setup shows strong confluence with zone confirmation."
        
    async def _get_position_summary(self) -> str:
        return "12 positions open. 6 in profit. 6 monitoring."
        
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
        elif action == 'momentum_boost':
            current_tps = event.data.get('current_tps', 0)
            previous_tps = event.data.get('previous_tps', 0)
            increase = current_tps - previous_tps
            await self.post_momentum_boost(current_tps, previous_tps, increase)
            response_data['status'] = 'posted'
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
            
        entry_data = event.data
        await self.post_entry_breakdown(entry_data)
        
    async def handle_tps_update(self, event: Event):
        """Handle TPS updates for marketing"""
        if not self.running:
            return
            
        tps = event.data.get('tps', 0)
        previous_tps = event.data.get('previous_tps', 0)
        
        # Update TPS history
        tps_history = await self.state_manager.get('tps_history', [])
        tps_history.append(tps)
        if len(tps_history) > 100:
            tps_history = tps_history[-100:]
        await self.state_manager.set('tps_history', tps_history)
        
        # Check for momentum boost
        increase = tps - previous_tps
        if increase >= self.marketing_enhancements['momentum_boost']['threshold']:
            await self.post_momentum_boost(tps, previous_tps, increase)
            
    async def publish_marketing_status(self):
        """Publish marketing status"""
        status_data = {
            'last_scam_warning': self.last_scam_warning,
            'last_weekly_warning': self.last_weekly_warning,
            'last_momentum_post': self.last_momentum_post,
            'streak_count': self.streak_count,
            'daily_posts': self.daily_posts,
            'scam_warning_enabled': self.scam_warning_config['enabled'],
            'marketing_enhancements': self.marketing_enhancements,
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
            'last_scam_warning': self.last_scam_warning,
            'last_weekly_warning': self.last_weekly_warning,
            'last_momentum_post': self.last_momentum_post,
            'streak_count': self.streak_count,
            'marketing_enhancements': self.marketing_enhancements,
            'timestamp': datetime.now().isoformat()
        }
