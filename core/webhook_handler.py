# core/webhook_handler.py
# AlphaEdge V13.0.7 – Webhook Handler
# Item 5: Webhook Handler for TradingView Alerts

import logging
import json
from aiohttp import web
from datetime import datetime
from typing import Dict, Any

from core.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Webhook Handler – Receives signals from TradingView alerts
    Item 5: Webhook Handler for TradingView Integration
    """
    
    def __init__(self, event_bus: EventBus, port: int = 8080):
        self.event_bus = event_bus
        self.port = port
        self.app = web.Application()
        self.app.router.add_post('/webhook', self.handle_webhook)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)
        self.runner = None
        self.site = None
        self._running = False
        
        # Webhook statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'last_request': None,
            'last_signal': None
        }
        
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.Response(text="OK", status=200)
        
    async def handle_status(self, request: web.Request) -> web.Response:
        """Status endpoint"""
        return web.json_response({
            'status': 'running' if self._running else 'stopped',
            'port': self.port,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        })
        
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """
        Process incoming webhook from TradingView
        """
        self.stats['total_requests'] += 1
        
        try:
            data = await request.json()
            
            # Parse alert data
            alert_type = data.get('type', 'unknown')
            ticker = data.get('ticker', '')
            message = data.get('message', '')
            tps = data.get('tps', 0)
            price = data.get('price', 0)
            score = data.get('score', 0)
            direction = data.get('direction', '')
            zone_type = data.get('zone_type', '')
            signal = data.get('signal', '')
            
            logger.info(f"📨 Webhook received: {alert_type} | {ticker}")
            logger.debug(f"   Data: {data}")
            
            # Update stats
            self.stats['last_request'] = datetime.now().isoformat()
            self.stats['last_signal'] = {
                'type': alert_type,
                'ticker': ticker,
                'timestamp': datetime.now().isoformat()
            }
            
            # Handle different alert types
            if alert_type == 'ae_buy' or alert_type == 'combined_entry':
                # BUY signal from TradingView
                await self.event_bus.publish(Event(
                    event_type="webhook_buy_signal",
                    data={
                        'type': alert_type,
                        'ticker': ticker,
                        'tps': tps,
                        'price': price,
                        'score': score,
                        'zone_type': zone_type,
                        'signal': signal,
                        'source': 'tradingview',
                        'timestamp': datetime.now().isoformat()
                    },
                    source="webhook_handler"
                ))
                logger.info(f"🔺 BUY signal forwarded: {ticker} (TPS: {tps})")
                self.stats['successful_requests'] += 1
                
            elif alert_type == 'ae_sell' or alert_type == 'combined_exit':
                # SELL signal from TradingView
                await self.event_bus.publish(Event(
                    event_type="webhook_sell_signal",
                    data={
                        'type': alert_type,
                        'ticker': ticker,
                        'tps': tps,
                        'price': price,
                        'score': score,
                        'signal': signal,
                        'source': 'tradingview',
                        'timestamp': datetime.now().isoformat()
                    },
                    source="webhook_handler"
                ))
                logger.info(f"🔻 SELL signal forwarded: {ticker} (TPS: {tps})")
                self.stats['successful_requests'] += 1
                
            elif alert_type == 'elite_zone_approach':
                # Elite zone approach alert
                await self.event_bus.publish(Event(
                    event_type="webhook_elite_zone",
                    data={
                        'type': alert_type,
                        'ticker': ticker,
                        'score': score,
                        'direction': direction,
                        'price': price,
                        'source': 'tradingview',
                        'timestamp': datetime.now().isoformat()
                    },
                    source="webhook_handler"
                ))
                logger.info(f"⭐ Elite zone approach: {ticker} (Score: {score})")
                self.stats['successful_requests'] += 1
                
            elif alert_type == 'tps_alert':
                # TPS threshold alert
                await self.event_bus.publish(Event(
                    event_type="webhook_tps_alert",
                    data={
                        'type': alert_type,
                        'ticker': ticker,
                        'tps': tps,
                        'threshold': data.get('threshold', 82),
                        'source': 'tradingview',
                        'timestamp': datetime.now().isoformat()
                    },
                    source="webhook_handler"
                ))
                logger.info(f"📊 TPS alert: {ticker} (TPS: {tps})")
                self.stats['successful_requests'] += 1
                
            else:
                # Unknown alert type - log but don't forward
                logger.warning(f"Unknown alert type: {alert_type}")
                self.stats['failed_requests'] += 1
                return web.Response(text="Unknown alert type", status=400)
                
            return web.Response(text="OK", status=200)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            self.stats['failed_requests'] += 1
            return web.Response(text="Invalid JSON", status=400)
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self.stats['failed_requests'] += 1
            return web.Response(text=f"Error: {str(e)}", status=500)
            
    async def start(self):
        """Start webhook server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            self._running = True
            logger.info(f"🚀 Webhook server running on port {self.port}")
            logger.info(f"   Endpoint: http://YOUR_BOT_IP:{self.port}/webhook")
            logger.info(f"   Health:   http://YOUR_BOT_IP:{self.port}/health")
            logger.info(f"   Status:   http://YOUR_BOT_IP:{self.port}/status")
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            raise
            
    async def stop(self):
        """Stop webhook server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            self._running = False
            logger.info("🛑 Webhook server stopped")
        except Exception as e:
            logger.error(f"Error stopping webhook server: {e}")
